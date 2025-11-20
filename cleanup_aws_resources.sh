#!/bin/bash
# AWS Cluster Deprovision Script
# Usage: 
#   ./aws.sh                         # Uses defaults (72 hours ago cutoff)
#   ./aws.sh --profile myprofile     # Uses specified AWS profile
#   ./aws.sh --cutoff "24 hours ago" # Custom age cutoff for cleanup
#   ./aws.sh --profile myprofile --cutoff "1 week ago" # Combined options
#
# Environment variables (with defaults):
#   ARTIFACTS=/tmp/artifacts                    # Directory for logs and metadata
#   CLUSTER_TTL="72 hours ago"                  # Age cutoff for cluster cleanup
#   AWS_PROFILE=""                              # AWS profile to use (optional)
#   AWS_SHARED_CREDENTIALS_FILE=~/.aws/credentials # AWS credentials file
#   HYPERSHIFT_BASE_DOMAIN=origin-ci-int-aws.dev.rhcloud.com # Hypershift domain

set -o errexit
set -o nounset
set -o pipefail

# Command line argument parsing
AWS_PROFILE="${AWS_PROFILE:-}"
CUTOFF_TIME=""

while [[ $# -gt 0 ]]; do
    case $1 in
        --profile)
            AWS_PROFILE="$2"
            shift 2
            ;;
        --cutoff)
            CUTOFF_TIME="$2"
            shift 2
            ;;
        --help|-h)
            echo "Usage: $0 [OPTIONS]"
            echo ""
            echo "Options:"
            echo "  --profile PROFILE    Use specified AWS profile"
            echo "  --cutoff TIME        Age cutoff for cleanup (e.g., '24 hours ago', '1 week ago')"
            echo "  --help, -h          Show this help message"
            echo ""
            echo "Examples:"
            echo "  $0                              # Default cleanup (72 hours ago)"
            echo "  $0 --cutoff '24 hours ago'      # Clean resources older than 24 hours"
            echo "  $0 --profile prod --cutoff '1 week ago'"
            echo ""
            echo "Environment variables:"
            echo "  ARTIFACTS                     Directory for logs (default: /tmp/artifacts)"
            echo "  AWS_PROFILE                   AWS profile to use"
            echo "  CLUSTER_TTL                   Default age cutoff (default: '72 hours ago')"
            exit 0
            ;;
        *)
            echo "Unknown option: $1" >&2
            echo "Use --help for usage information" >&2
            exit 1
            ;;
    esac
done

# Helper function to run AWS CLI commands with profile support
function aws_cmd() {
    if [[ -n "${AWS_PROFILE}" ]]; then
        aws --profile "${AWS_PROFILE}" "$@"
    else
        aws "$@"
    fi
}

trap finish TERM QUIT

function finish {
    CHILDREN=$(jobs -p)
    if test -n "${CHILDREN}"; then
        kill ${CHILDREN} && wait
    fi
    exit
}

function queue() {
    local LIVE="$(jobs | wc -l)"
    while [[ "${LIVE}" -ge 2 ]]; do
        sleep 1
        LIVE="$(jobs | wc -l)"
    done
    echo "${@}"
    "${@}" &
}

function retry() {
    local retries=5
    local wait=5
    local n=0
    until "$@"; do
        n=$((n+1))
        if [[ $n -ge $retries ]]; then
            echo "Command failed after $n attempts: $*" >&2
            return 1
        fi
        echo "Retry $n/$retries for: $*" >&2
        sleep $((wait**n))
    done
}

function force_cleanup_vpc() {
    local region="$1"
    local cluster="$2"

    echo "Force-cleaning VPCs for cluster $cluster in region $region"

    vpcs=$(aws_cmd ec2 describe-vpcs --region "$region" \
        --filters "Name=tag:kubernetes.io/cluster/${cluster},Values=owned" \
        --query 'Vpcs[].VpcId' --output text || true)

    for vpc in $vpcs; do
        echo "Cleaning VPC $vpc"

        # Delete NAT gateways
        echo "Cleaning up NAT gateways for VPC $vpc"
        for nat in $(aws_cmd ec2 describe-nat-gateways --region "$region" --filter Name=vpc-id,Values=$vpc --query 'NatGateways[].NatGatewayId' --output text || true); do
            echo "Deleting NAT gateway $nat"
            retry aws_cmd ec2 delete-nat-gateway --region "$region" --nat-gateway-id "$nat" || true
        done

        # Detach and delete IGWs
        echo "Cleaning up IGWs for VPC $vpc"
        for igw in $(aws_cmd ec2 describe-internet-gateways --region "$region" --filter Name=attachment.vpc-id,Values=$vpc --query 'InternetGateways[].InternetGatewayId' --output text || true); do
            echo "Detaching and deleting IGW $igw"
            retry aws_cmd ec2 detach-internet-gateway --region "$region" --internet-gateway-id "$igw" --vpc-id "$vpc" || true
            retry aws_cmd ec2 delete-internet-gateway --region "$region" --internet-gateway-id "$igw" || true
        done

        # Delete VPC endpoints
        echo "Cleaning up VPC endpoints for VPC $vpc"
        for vpce in $(aws_cmd ec2 describe-vpc-endpoints --region "$region" --filters "Name=vpc-id,Values=$vpc" --query 'VpcEndpoints[].VpcEndpointId' --output text || true); do
            echo "Deleting VPC endpoint $vpce"
            retry aws_cmd ec2 delete-vpc-endpoint --region "$region" --vpc-endpoint-id "$vpce" || true
        done

        # Delete VPC peering connections
        echo "Cleaning up VPC peering connections for VPC $vpc"
        for pcx in $(aws_cmd ec2 describe-vpc-peering-connections --region "$region" --filters "Name=requester-vpc-info.vpc-id,Values=$vpc" "Name=status-code,Values=active,pending-acceptance" --query 'VpcPeeringConnections[].VpcPeeringConnectionId' --output text || true); do
            echo "Deleting VPC peering connection $pcx"
            retry aws_cmd ec2 delete-vpc-peering-connection --region "$region" --vpc-peering-connection-id "$pcx" || true
        done
        for pcx in $(aws_cmd ec2 describe-vpc-peering-connections --region "$region" --filters "Name=accepter-vpc-info.vpc-id,Values=$vpc" "Name=status-code,Values=active,pending-acceptance" --query 'VpcPeeringConnections[].VpcPeeringConnectionId' --output text || true); do
            echo "Deleting VPC peering connection $pcx"
            retry aws_cmd ec2 delete-vpc-peering-connection --region "$region" --vpc-peering-connection-id "$pcx" || true
        done

        # Delete ENIs (Elastic Network Interfaces) that might prevent subnet deletion
        echo "Cleaning up ENIs for VPC $vpc"
        # First pass: delete available ENIs
        for eni in $(aws_cmd ec2 describe-network-interfaces --region "$region" --filters "Name=vpc-id,Values=$vpc" --query 'NetworkInterfaces[?Status==`available`].NetworkInterfaceId' --output text || true); do
            if [[ -n "$eni" && "$eni" != "None" ]]; then
                echo "Deleting available ENI $eni"
                retry aws_cmd ec2 delete-network-interface --region "$region" --network-interface-id "$eni" || true
            fi
        done
        
        # Second pass: force detach and delete in-use ENIs (except those managed by AWS services)
        for eni in $(aws_cmd ec2 describe-network-interfaces --region "$region" --filters "Name=vpc-id,Values=$vpc" --query 'NetworkInterfaces[?Status==`in-use` && !starts_with(Description, `ELB`) && !starts_with(Description, `AWS`) && !starts_with(Description, `RDSNetworkInterface`)].NetworkInterfaceId' --output text || true); do
            if [[ -n "$eni" && "$eni" != "None" ]]; then
                echo "Force detaching and deleting in-use ENI $eni"
                
                # Get attachment info
                attachment_id=$(aws_cmd ec2 describe-network-interfaces --region "$region" --network-interface-ids "$eni" --query 'NetworkInterfaces[0].Attachment.AttachmentId' --output text 2>/dev/null || true)
                if [[ -n "$attachment_id" && "$attachment_id" != "None" && "$attachment_id" != "null" ]]; then
                    echo "Detaching ENI $eni (attachment: $attachment_id)"
                    aws_cmd ec2 detach-network-interface --region "$region" --attachment-id "$attachment_id" --force || true
                    sleep 5  # Wait for detachment
                fi
                
                retry aws_cmd ec2 delete-network-interface --region "$region" --network-interface-id "$eni" || true
            fi
        done

        # Delete subnets with comprehensive cleanup
        echo "Cleaning up subnets for VPC $vpc"
        for subnet in $(aws_cmd ec2 describe-subnets --region "$region" --filter Name=vpc-id,Values=$vpc --query 'Subnets[].SubnetId' --output text || true); do
            if [[ -n "$subnet" && "$subnet" != "None" ]]; then
                echo "Processing subnet $subnet"
                
                # Check for remaining ENIs in this subnet and clean them up
                for eni in $(aws_cmd ec2 describe-network-interfaces --region "$region" --filters "Name=subnet-id,Values=$subnet" --query 'NetworkInterfaces[].NetworkInterfaceId' --output text || true); do
                    if [[ -n "$eni" && "$eni" != "None" ]]; then
                        echo "Found remaining ENI $eni in subnet $subnet, cleaning up..."
                        eni_description=$(aws_cmd ec2 describe-network-interfaces --region "$region" --network-interface-ids "$eni" --query 'NetworkInterfaces[0].Description' --output text 2>/dev/null || echo "")
                        echo "ENI description: $eni_description"
                        
                        # Skip AWS-managed ENIs that shouldn't be manually deleted
                        if [[ "$eni_description" =~ ^(ELB|AWS|RDSNetworkInterface|ElastiCache|Lambda) ]]; then
                            echo "Skipping AWS-managed ENI $eni"
                            continue
                        fi
                        
                        # Get attachment info and detach if needed
                        attachment_id=$(aws_cmd ec2 describe-network-interfaces --region "$region" --network-interface-ids "$eni" --query 'NetworkInterfaces[0].Attachment.AttachmentId' --output text 2>/dev/null || true)
                        if [[ -n "$attachment_id" && "$attachment_id" != "None" && "$attachment_id" != "null" ]]; then
                            echo "Force detaching ENI $eni from subnet $subnet"
                            aws_cmd ec2 detach-network-interface --region "$region" --attachment-id "$attachment_id" --force || true
                            sleep 3
                        fi
                        
                        echo "Deleting ENI $eni"
                        retry aws_cmd ec2 delete-network-interface --region "$region" --network-interface-id "$eni" || true
                    fi
                done
                
                echo "Deleting subnet $subnet"
                if ! retry aws_cmd ec2 delete-subnet --region "$region" --subnet-id "$subnet"; then
                    echo "Failed to delete subnet $subnet, checking dependencies..."
                    aws_cmd ec2 describe-network-interfaces --region "$region" --filters "Name=subnet-id,Values=$subnet" --query 'NetworkInterfaces[].{Id:NetworkInterfaceId,Status:Status,Description:Description,InstanceId:Attachment.InstanceId}' --output table || true
                fi
            fi
        done

        # Delete route tables (except main) - handle dependencies first
        echo "Cleaning up route tables for VPC $vpc"
        
        # Get all route tables for this VPC
        all_route_tables=$(aws_cmd ec2 describe-route-tables --region "$region" --filters "Name=vpc-id,Values=$vpc" --query 'RouteTables[].RouteTableId' --output text || true)
        
        for rtb in $all_route_tables; do
            if [[ -n "$rtb" && "$rtb" != "None" ]]; then
                echo "Checking route table $rtb"
                
                # Check if this is the main route table (cannot be deleted)
                is_main=$(aws_cmd ec2 describe-route-tables --region "$region" --route-table-ids "$rtb" --query 'RouteTables[0].Associations[?Main==`true`] | length(@)' --output text 2>/dev/null || echo "0")
                
                if [[ "$is_main" -gt 0 ]]; then
                    echo "Skipping main route table $rtb"
                    continue
                fi
                
                echo "Processing non-main route table $rtb"
                
                # Get detailed route table info for debugging
                echo "Route table $rtb details:"
                aws_cmd ec2 describe-route-tables --region "$region" --route-table-ids "$rtb" --query 'RouteTables[0].{Routes:Routes[].{Destination:DestinationCidrBlock,DestinationIPv6:DestinationIpv6CidrBlock,Gateway:GatewayId,Origin:Origin,State:State},Associations:Associations[].{AssociationId:RouteTableAssociationId,SubnetId:SubnetId,Main:Main}}' --output json || true
                
                # Step 1: Disassociate all subnet associations
                echo "Disassociating subnet associations for route table $rtb"
                associations=$(aws_cmd ec2 describe-route-tables --region "$region" --route-table-ids "$rtb" --query 'RouteTables[0].Associations[?Main!=`true` && SubnetId!=null].RouteTableAssociationId' --output text 2>/dev/null || true)
                
                for assoc in $associations; do
                    if [[ -n "$assoc" && "$assoc" != "None" ]]; then
                        echo "Disassociating route table association $assoc"
                        if retry aws_cmd ec2 disassociate-route-table --region "$region" --association-id "$assoc"; then
                            echo "✓ Successfully disassociated $assoc"
                        else
                            echo "✗ Failed to disassociate $assoc"
                        fi
                    fi
                done
                
                # Step 2: Delete all custom routes (non-local, non-propagated)
                echo "Deleting custom routes from route table $rtb"
                
                # Delete IPv4 routes
                ipv4_routes=$(aws_cmd ec2 describe-route-tables --region "$region" --route-table-ids "$rtb" --query 'RouteTables[0].Routes[?Origin==`CreateRoute` && DestinationCidrBlock!=null].DestinationCidrBlock' --output text 2>/dev/null || true)
                for route in $ipv4_routes; do
                    if [[ -n "$route" && "$route" != "None" ]]; then
                        echo "Deleting IPv4 route $route from route table $rtb"
                        if retry aws_cmd ec2 delete-route --region "$region" --route-table-id "$rtb" --destination-cidr-block "$route"; then
                            echo "✓ Successfully deleted route $route"
                        else
                            echo "✗ Failed to delete route $route"
                        fi
                    fi
                done
                
                # Delete IPv6 routes
                ipv6_routes=$(aws_cmd ec2 describe-route-tables --region "$region" --route-table-ids "$rtb" --query 'RouteTables[0].Routes[?Origin==`CreateRoute` && DestinationIpv6CidrBlock!=null].DestinationIpv6CidrBlock' --output text 2>/dev/null || true)
                for route in $ipv6_routes; do
                    if [[ -n "$route" && "$route" != "None" ]]; then
                        echo "Deleting IPv6 route $route from route table $rtb"
                        if retry aws_cmd ec2 delete-route --region "$region" --route-table-id "$rtb" --destination-ipv6-cidr-block "$route"; then
                            echo "✓ Successfully deleted IPv6 route $route"
                        else
                            echo "✗ Failed to delete IPv6 route $route"
                        fi
                    fi
                done
                
                # Delete prefix list routes
                prefix_routes=$(aws_cmd ec2 describe-route-tables --region "$region" --route-table-ids "$rtb" --query 'RouteTables[0].Routes[?Origin==`CreateRoute` && DestinationPrefixListId!=null].DestinationPrefixListId' --output text 2>/dev/null || true)
                for route in $prefix_routes; do
                    if [[ -n "$route" && "$route" != "None" ]]; then
                        echo "Deleting prefix list route $route from route table $rtb"
                        retry aws_cmd ec2 delete-route --region "$region" --route-table-id "$rtb" --destination-prefix-list-id "$route" || true
                    fi
                done
                
                # Wait a moment for route deletions to propagate
                sleep 3
                
                # Step 3: Try to delete the route table
                echo "Attempting to delete route table $rtb"
                if retry aws_cmd ec2 delete-route-table --region "$region" --route-table-id "$rtb"; then
                    echo "✓ Successfully deleted route table $rtb"
                else
                    echo "✗ Failed to delete route table $rtb - checking remaining dependencies"
                    echo "Remaining dependencies for route table $rtb:"
                    aws_cmd ec2 describe-route-tables --region "$region" --route-table-ids "$rtb" --query 'RouteTables[0].{Routes:Routes,Associations:Associations}' --output json || true
                fi
            fi
        done

        # Delete security groups (except default) - handle cross-references
        echo "Cleaning up security groups for VPC $vpc"
        
        # First, remove all ingress and egress rules that reference other security groups
        for sg in $(aws_cmd ec2 describe-security-groups --region "$region" --filter Name=vpc-id,Values=$vpc --query 'SecurityGroups[?GroupName!=`default`].GroupId' --output text || true); do
            echo "Cleaning rules for security group $sg"
            
            # Get and revoke ingress rules
            ingress_rules=$(aws_cmd ec2 describe-security-groups --region "$region" --group-ids "$sg" --query 'SecurityGroups[].IpPermissions' --output json || echo '[]')
            if [[ "$ingress_rules" != "[]" && "$ingress_rules" != "null" ]]; then
                echo "Revoking ingress rules for security group $sg"
                aws_cmd ec2 revoke-security-group-ingress --region "$region" --group-id "$sg" --ip-permissions "$ingress_rules" || true
            fi
            
            # Get and revoke egress rules (except the default allow-all rule)
            egress_rules=$(aws_cmd ec2 describe-security-groups --region "$region" --group-ids "$sg" --query 'SecurityGroups[].IpPermissionsEgress[?!(IpProtocol==`-1` && IpRanges[0].CidrIp==`0.0.0.0/0`)]' --output json || echo '[]')
            if [[ "$egress_rules" != "[]" && "$egress_rules" != "null" ]]; then
                echo "Revoking egress rules for security group $sg"
                aws_cmd ec2 revoke-security-group-egress --region "$region" --group-id "$sg" --ip-permissions "$egress_rules" || true
            fi
        done
        
        # Now delete the security groups
        for sg in $(aws_cmd ec2 describe-security-groups --region "$region" --filter Name=vpc-id,Values=$vpc --query 'SecurityGroups[?GroupName!=`default`].GroupId' --output text || true); do
            echo "Deleting security group $sg"
            retry aws_cmd ec2 delete-security-group --region "$region" --group-id "$sg" || true
        done

        # Additional dependency cleanup before VPC deletion
        echo "Performing additional dependency cleanup for VPC $vpc"
        
        # Delete Load Balancers (ELB, ALB, NLB)
        echo "Cleaning up load balancers for VPC $vpc"
        for elb in $(aws_cmd elb describe-load-balancers --region "$region" --query "LoadBalancerDescriptions[?VPCId=='$vpc'].LoadBalancerName" --output text 2>/dev/null || true); do
            if [[ -n "$elb" && "$elb" != "None" ]]; then
                echo "Deleting classic load balancer $elb"
                retry aws_cmd elb delete-load-balancer --region "$region" --load-balancer-name "$elb" || true
            fi
        done
        
        for alb in $(aws_cmd elbv2 describe-load-balancers --region "$region" --query "LoadBalancers[?VpcId=='$vpc'].LoadBalancerArn" --output text 2>/dev/null || true); do
            if [[ -n "$alb" && "$alb" != "None" ]]; then
                echo "Deleting ALB/NLB $alb"
                retry aws_cmd elbv2 delete-load-balancer --region "$region" --load-balancer-arn "$alb" || true
            fi
        done
        
        # Delete RDS subnet groups
        echo "Cleaning up RDS subnet groups for VPC $vpc"
        for sg in $(aws_cmd rds describe-db-subnet-groups --region "$region" --query "DBSubnetGroups[?VpcId=='$vpc'].DBSubnetGroupName" --output text 2>/dev/null || true); do
            if [[ -n "$sg" && "$sg" != "None" ]]; then
                echo "Deleting RDS subnet group $sg"
                retry aws_cmd rds delete-db-subnet-group --region "$region" --db-subnet-group-name "$sg" || true
            fi
        done
        
        # Delete ElastiCache subnet groups
        echo "Cleaning up ElastiCache subnet groups for VPC $vpc"
        for csg in $(aws_cmd elasticache describe-cache-subnet-groups --region "$region" --query "CacheSubnetGroups[?VpcId=='$vpc'].CacheSubnetGroupName" --output text 2>/dev/null || true); do
            if [[ -n "$csg" && "$csg" != "None" ]]; then
                echo "Deleting ElastiCache subnet group $csg"
                retry aws_cmd elasticache delete-cache-subnet-group --region "$region" --cache-subnet-group-name "$csg" || true
            fi
        done
        
        # Delete EFS mount targets
        echo "Cleaning up EFS mount targets for VPC $vpc"
        for mt in $(aws_cmd efs describe-mount-targets --region "$region" --query "MountTargets[?VpcId=='$vpc'].MountTargetId" --output text 2>/dev/null || true); do
            if [[ -n "$mt" && "$mt" != "None" ]]; then
                echo "Deleting EFS mount target $mt"
                retry aws_cmd efs delete-mount-target --region "$region" --mount-target-id "$mt" || true
            fi
        done
        
        # Delete VPN gateways
        echo "Cleaning up VPN gateways for VPC $vpc"
        for vgw in $(aws_cmd ec2 describe-vpn-gateways --region "$region" --filters "Name=attachment.vpc-id,Values=$vpc" --query 'VpnGateways[].VpnGatewayId' --output text || true); do
            if [[ -n "$vgw" && "$vgw" != "None" ]]; then
                echo "Detaching VPN gateway $vgw from VPC $vpc"
                retry aws_cmd ec2 detach-vpn-gateway --region "$region" --vpn-gateway-id "$vgw" --vpc-id "$vpc" || true
            fi
        done
        
        # Delete Network ACLs (except default)
        echo "Cleaning up Network ACLs for VPC $vpc"
        for nacl in $(aws_cmd ec2 describe-network-acls --region "$region" --filters "Name=vpc-id,Values=$vpc" --query 'NetworkAcls[?IsDefault!=`true`].NetworkAclId' --output text || true); do
            if [[ -n "$nacl" && "$nacl" != "None" ]]; then
                echo "Deleting Network ACL $nacl"
                retry aws_cmd ec2 delete-network-acl --region "$region" --network-acl-id "$nacl" || true
            fi
        done
        
        # Wait for async deletions to complete
        echo "Waiting for async resource deletions to complete..."
        sleep 15
        
        # Final comprehensive dependency check
        echo "Performing final dependency check for VPC $vpc"
        
        # Check for any remaining ENIs
        remaining_enis=$(aws_cmd ec2 describe-network-interfaces --region "$region" --filters "Name=vpc-id,Values=$vpc" --query 'NetworkInterfaces[].NetworkInterfaceId' --output text || true)
        if [[ -n "$remaining_enis" && "$remaining_enis" != "None" ]]; then
            echo "WARNING: Found remaining ENIs in VPC $vpc:"
            aws_cmd ec2 describe-network-interfaces --region "$region" --filters "Name=vpc-id,Values=$vpc" --query 'NetworkInterfaces[].{Id:NetworkInterfaceId,Status:Status,Description:Description,InstanceId:Attachment.InstanceId,SubnetId:SubnetId}' --output table || true
            
            # Final attempt to clean up remaining ENIs
            for eni in $remaining_enis; do
                if [[ -n "$eni" && "$eni" != "None" ]]; then
                    echo "Final cleanup attempt for ENI $eni"
                    attachment_id=$(aws_cmd ec2 describe-network-interfaces --region "$region" --network-interface-ids "$eni" --query 'NetworkInterfaces[0].Attachment.AttachmentId' --output text 2>/dev/null || true)
                    if [[ -n "$attachment_id" && "$attachment_id" != "None" && "$attachment_id" != "null" ]]; then
                        aws_cmd ec2 detach-network-interface --region "$region" --attachment-id "$attachment_id" --force || true
                        sleep 5
                    fi
                    aws_cmd ec2 delete-network-interface --region "$region" --network-interface-id "$eni" || true
                fi
            done
            sleep 5
        fi
        
        # Check for remaining subnets
        remaining_subnets=$(aws_cmd ec2 describe-subnets --region "$region" --filters "Name=vpc-id,Values=$vpc" --query 'Subnets[].SubnetId' --output text || true)
        if [[ -n "$remaining_subnets" && "$remaining_subnets" != "None" ]]; then
            echo "WARNING: Found remaining subnets in VPC $vpc: $remaining_subnets"
            for subnet in $remaining_subnets; do
                if [[ -n "$subnet" && "$subnet" != "None" ]]; then
                    echo "Final cleanup attempt for subnet $subnet"
                    aws_cmd ec2 delete-subnet --region "$region" --subnet-id "$subnet" || true
                fi
            done
            sleep 3
        fi
        
        # Finally delete the VPC
        echo "Attempting final VPC deletion: $vpc"
        if retry aws_cmd ec2 delete-vpc --region "$region" --vpc-id "$vpc"; then
            echo "✓ Successfully deleted VPC $vpc"
        else
            echo "✗ Failed to delete VPC $vpc - listing remaining dependencies for manual cleanup"
            echo "========== REMAINING DEPENDENCIES FOR VPC $vpc =========="
            
            echo "Network Interfaces:"
            aws_cmd ec2 describe-network-interfaces --region "$region" --filters "Name=vpc-id,Values=$vpc" --query 'NetworkInterfaces[].{Id:NetworkInterfaceId,Status:Status,Description:Description,InstanceId:Attachment.InstanceId,SubnetId:SubnetId}' --output table || true
            
            echo "Subnets:"
            aws_cmd ec2 describe-subnets --region "$region" --filters "Name=vpc-id,Values=$vpc" --query 'Subnets[].{SubnetId:SubnetId,State:State,AvailabilityZone:AvailabilityZone}' --output table || true
            
            echo "Route Tables:"
            aws_cmd ec2 describe-route-tables --region "$region" --filters "Name=vpc-id,Values=$vpc" --query 'RouteTables[].{RouteTableId:RouteTableId,Main:Associations[0].Main,AssociationCount:length(Associations)}' --output table || true
            
            echo "Security Groups:"
            aws_cmd ec2 describe-security-groups --region "$region" --filters "Name=vpc-id,Values=$vpc" --query 'SecurityGroups[].{GroupId:GroupId,GroupName:GroupName,Description:Description}' --output table || true
            
            echo "Internet Gateways:"
            aws_cmd ec2 describe-internet-gateways --region "$region" --filters "Name=attachment.vpc-id,Values=$vpc" --query 'InternetGateways[].{Id:InternetGatewayId,State:Attachments[0].State}' --output table || true
            
            echo "NAT Gateways:"
            aws_cmd ec2 describe-nat-gateways --region "$region" --filters "Name=vpc-id,Values=$vpc" --query 'NatGateways[].{Id:NatGatewayId,State:State,SubnetId:SubnetId}' --output table || true
            
            echo "VPC Endpoints:"
            aws_cmd ec2 describe-vpc-endpoints --region "$region" --filters "Name=vpc-id,Values=$vpc" --query 'VpcEndpoints[].{Id:VpcEndpointId,State:State,ServiceName:ServiceName}' --output table || true
            
            echo "========== END DEPENDENCY LIST =========="
        fi
        echo "Completed cleanup for VPC $vpc"
        echo "========================================"
    done
}

function force_cleanup_route53() {
    local cluster="$1"

    zones=$(aws_cmd route53 list-hosted-zones --query "HostedZones[?Name == '${cluster}.${HYPERSHIFT_BASE_DOMAIN}.'].Id" --output text || true)
    for zone in $zones; do
        records=$(aws_cmd route53 list-resource-record-sets --hosted-zone-id "$zone" --query "ResourceRecordSets[?Type != 'NS' && Type != 'SOA']" --output json || true)
        for record in $(echo "$records" | jq -r '.[] | @base64'); do
            rname=$(echo "$record" | base64 --decode | jq -r .Name)
            rtype=$(echo "$record" | base64 --decode | jq -r .Type)
            aws_cmd route53 change-resource-record-sets \
                --hosted-zone-id "$zone" \
                --change-batch "{\"Changes\":[{\"Action\":\"DELETE\",\"ResourceRecordSet\":$(echo "$record" | base64 --decode)}]}" || true
        done
        retry aws_cmd route53 delete-hosted-zone --id "$zone" || true
    done
}

function deprovision() {
    WORKDIR="${1}"
    REGION="$(cat ${WORKDIR}/metadata.json|jq .aws.region -r)"
    INFRA_ID="$(cat ${WORKDIR}/metadata.json|jq '.aws.identifier[0]|keys[0]' -r|cut -d '/' -f3|tr -d '\n')"

    if [[ -n ${HYPERSHIFT_PRUNER:-} ]]; then
        HYPERSHIFT_BASE_DOMAIN="${HYPERSHIFT_BASE_DOMAIN:-origin-ci-int-aws.dev.rhcloud.com}"
        timeout --signal=SIGQUIT 30m hypershift destroy infra aws --aws-creds "${AWS_SHARED_CREDENTIALS_FILE}" --infra-id "${INFRA_ID}" --base-domain "${HYPERSHIFT_BASE_DOMAIN}" --region "${REGION}" || touch "${WORKDIR}/failure"
        timeout --signal=SIGQUIT 30m hypershift destroy iam aws --aws-creds "${AWS_SHARED_CREDENTIALS_FILE}" --infra-id "${INFRA_ID}" --region "${REGION}" || touch "${WORKDIR}/failure"
    else
        if command -v openshift-install >/dev/null 2>&1; then
            timeout --signal=SIGQUIT 60m openshift-install --dir "${WORKDIR}" --log-level error destroy cluster && touch "${WORKDIR}/success" || touch "${WORKDIR}/failure"
        else
            echo "Warning: openshift-install not found, skipping standard cluster destroy for ${WORKDIR##*/}"
            touch "${WORKDIR}/failure"
        fi
    fi

    # Failsafe: if cluster destroy failed, clean VPCs and Route53
    if [[ -f "${WORKDIR}/failure" ]]; then
        cluster="${WORKDIR##*/}"
        force_cleanup_vpc "${REGION}" "${cluster}"
        force_cleanup_route53 "${cluster}"
    fi
}

# HYPERSHIFT CLUSTER CLEANUP (configurable cutoff)
had_failure=0
# Check if hostedcluster resource type exists before attempting cleanup
if oc api-resources | grep -q "hostedclusters"; then
    echo "Hypershift hostedcluster resource found, checking for old clusters (older than ${CLUSTER_TTL})..."
    # Convert cutoff time to seconds ago for jq timestamp comparison
    cutoff_seconds=$(( $(date +%s) - $(date -d "${CLUSTER_TTL}" +%s) ))
    hostedclusters="$(oc get hostedcluster -n clusters -o json 2>/dev/null | jq -r --argjson timestamp ${cutoff_seconds} '.items[] | select (.metadata.creationTimestamp | sub("\\..*";"Z") | sub("\\s";"T") | fromdate < now - $timestamp).metadata.name' 2>/dev/null || true)"
    for hostedcluster in $hostedclusters; do
        if [[ -n "$hostedcluster" ]]; then
            echo "Destroying hostedcluster: $hostedcluster"
            hypershift destroy cluster aws --aws-creds "${AWS_SHARED_CREDENTIALS_FILE}" --namespace clusters --name "${hostedcluster}" || had_failure=$((had_failure+1))
        fi
    done
else
    echo "Hypershift hostedcluster resource not found, skipping hypershift cleanup..."
fi
if [[ $had_failure -ne 0 ]]; then exit $had_failure; fi

# DEPENDENCY CHECKS
echo "Checking required dependencies..."
missing_deps=0

# Check for required commands
for cmd in aws jq date find; do
    if ! command -v "$cmd" >/dev/null 2>&1; then
        echo "ERROR: Required command '$cmd' not found in PATH" >&2
        missing_deps=$((missing_deps + 1))
    fi
done

# Check for optional commands  
for cmd in openshift-install hypershift oc; do
    if ! command -v "$cmd" >/dev/null 2>&1; then
        echo "WARNING: Optional command '$cmd' not found in PATH" >&2
    fi
done

if [[ $missing_deps -gt 0 ]]; then
    echo "ERROR: $missing_deps required dependencies missing. Exiting." >&2
    exit 1
fi

echo "Dependency check complete."

# MAIN CLUSTER DEPROVISION LOGIC
# Set default values for environment variables if not already set
ARTIFACTS="${ARTIFACTS:-/tmp/artifacts}"

# Use command line cutoff if provided, otherwise use environment variable, otherwise default
if [[ -n "${CUTOFF_TIME}" ]]; then
    CLUSTER_TTL="${CUTOFF_TIME}"
    echo "Using command line cutoff: ${CLUSTER_TTL}"
else
    CLUSTER_TTL="${CLUSTER_TTL:-72 hours ago}"
    echo "Using default cutoff: ${CLUSTER_TTL}"
fi

AWS_SHARED_CREDENTIALS_FILE="${AWS_SHARED_CREDENTIALS_FILE:-${HOME}/.aws/credentials}"
HYPERSHIFT_BASE_DOMAIN="${HYPERSHIFT_BASE_DOMAIN:-origin-ci-int-aws.dev.rhcloud.com}"

logdir="${ARTIFACTS}/deprovision"
mkdir -p "${logdir}"

# Set up logging to file
LOGFILE="${ARTIFACTS}/aws-deprovision-$(date +%Y%m%d-%H%M%S).log"
echo "AWS Deprovision Script started at $(date)" >&2
echo "Logging to: ${LOGFILE}" >&2
echo "Use 'tail -f ${LOGFILE}' to follow progress" >&2
echo "=======================================" >&2

# Redirect stdout to log file, keep stderr for important messages
exec 1> >(tee -a "${LOGFILE}")
exec 2> >(tee -a "${LOGFILE}" >&2)

aws_cluster_age_cutoff="$(TZ=":Africa/Abidjan" date --date="${CLUSTER_TTL}" '+%Y-%m-%dT%H:%M+0000')"
echo "deprovisioning clusters with an expirationDate before ${aws_cluster_age_cutoff} in AWS ..."

# Test AWS credentials before proceeding
echo "Testing AWS credentials and connectivity..."
if ! aws_cmd sts get-caller-identity >/dev/null 2>&1; then
    echo "ERROR: AWS credentials test failed. Please check your AWS configuration." >&2
    echo "Make sure you have valid AWS credentials configured." >&2
    echo "You can configure them using:" >&2
    echo "  - aws configure" >&2
    echo "  - AWS_PROFILE environment variable" >&2
    echo "  - --profile command line argument" >&2
    exit 1
fi

echo "AWS credentials verified. Discovering regions..."
regions=$(aws_cmd ec2 describe-regions --region us-east-1 --query "Regions[].{Name:RegionName}" --output text 2>/dev/null || echo "")
if [[ -z "$regions" ]]; then
    echo "ERROR: Failed to retrieve AWS regions. Check your AWS permissions." >&2
    exit 1
fi

echo "Found $(echo $regions | wc -w) AWS regions to check."

for region in $regions; do
    echo "deprovisioning in AWS region ${region} ..."
    # Clear previous clusters file and get VPCs for this region
    > /tmp/clusters
    if aws_cmd ec2 describe-vpcs --output json --region ${region} 2>/dev/null | jq --arg date "${aws_cluster_age_cutoff}" -r '.Vpcs[] | select(.Tags[]? | select(.Key == "expirationDate" and .Value < $date)) | .Tags[]? | select((.Key | startswith("kubernetes.io/cluster/")) and (.Value == "owned")) | .Key' > /tmp/clusters 2>/dev/null; then
        cluster_count=$(wc -l < /tmp/clusters)
        if [[ $cluster_count -gt 0 ]]; then
            echo "Found $cluster_count clusters to deprovision in region ${region}"
        else
            echo "No expired clusters found in region ${region}"
        fi
    else
        echo "Warning: Failed to query VPCs in region ${region}, skipping..."
        continue
    fi
    
    while read cluster; do
        if [[ -n "$cluster" ]]; then
            workdir="${logdir}/${cluster:22}"
            mkdir -p "${workdir}"
            cat <<-EOF >"${workdir}/metadata.json"
            {
                "aws":{
                    "region":"${region}",
                    "identifier":[
                        {"${cluster}": "owned"}
                    ]
                }
            }
EOF
            echo "will deprovision AWS cluster ${cluster} in region ${region}"
        fi
    done < /tmp/clusters
done

echo "Region discovery completed."
total_clusters=$(find "${logdir}" -mindepth 1 -maxdepth 1 -type d | wc -l)
echo "Total clusters identified for deprovision: ${total_clusters}"

if [[ $total_clusters -eq 0 ]]; then
    echo "No clusters found for deprovision. Proceeding to IAM cleanup only."
fi

# Check if openshift-install is available
if command -v openshift-install >/dev/null 2>&1; then
    echo "Using openshift-install version:"
    openshift-install version
else
    echo "Warning: openshift-install not found in PATH. Cluster destruction will use force cleanup methods."
fi

clusters=$( find "${logdir}" -mindepth 1 -type d )
for workdir in $(shuf <<< ${clusters}); do
    queue deprovision "${workdir}"
done

wait

# IAM USER CLEANUP (ci-op-* users older than cutoff time) - run after all cluster deprovisions complete
echo "Cleaning up old IAM users (older than ${CLUSTER_TTL})..."
cutoff="$(date -u -d "${CLUSTER_TTL}" --iso-8601=seconds)"
aws_cmd iam list-users --query "Users[?starts_with(UserName, 'ci-op-') && CreateDate < '${cutoff}'].UserName" --output text | tr '\t' '\n' | while read -r user; do
    if [[ -n "$user" ]]; then
        echo "Cleaning IAM user: $user"
        aws_cmd iam list-attached-user-policies --user-name "$user" --query 'AttachedPolicies[].PolicyArn' --output text | tr '\t' '\n' | while read -r policy; do
            [[ -n "$policy" ]] && aws_cmd iam detach-user-policy --user-name "$user" --policy-arn "$policy" || true
        done
        aws_cmd iam list-user-policies --user-name "$user" --query 'PolicyNames[]' --output text | tr '\t' '\n' | while read -r policy; do
            [[ -n "$policy" ]] && aws_cmd iam delete-user-policy --user-name "$user" --policy-name "$policy" || true
        done
        aws_cmd iam list-access-keys --user-name "$user" --query 'AccessKeyMetadata[].AccessKeyId' --output text | tr '\t' '\n' | while read -r key; do
            [[ -n "$key" ]] && aws_cmd iam delete-access-key --user-name "$user" --access-key-id "$key" || true
        done
        aws_cmd iam list-groups-for-user --user-name "$user" --query 'Groups[].GroupName' --output text | tr '\t' '\n' | while read -r group; do
            [[ -n "$group" ]] && aws_cmd iam remove-user-from-group --user-name "$user" --group-name "$group" || true
        done
        aws_cmd iam delete-user --user-name "$user" && echo "✓ Deleted: $user"
    fi
done

# CHECK DEPROVISION RESULTS
FAILED="$(find ${clusters} -name failure -printf '%H\n' | sort || true)"
if [[ -n "${FAILED}" ]]; then
    echo "Deprovision failed on the following clusters:"
    xargs --max-args 1 basename <<< $FAILED
    exit 1
fi

echo "Deprovision finished successfully"
