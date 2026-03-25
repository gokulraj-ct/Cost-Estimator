"""
AWS Pricing Service - AWS API Only (No Fallback)
"""

import boto3
import json
from functools import lru_cache


class AWSPricingService:
    """Fetch real-time AWS pricing - AWS API required"""
    
    REGION_MAP = {
        'us-east-1': 'US East (N. Virginia)',
        'us-east-2': 'US East (Ohio)',
        'us-west-1': 'US West (N. California)',
        'us-west-2': 'US West (Oregon)',
        'eu-west-1': 'EU (Ireland)',
        'eu-west-2': 'EU (London)',
        'eu-central-1': 'EU (Frankfurt)',
        'ap-southeast-1': 'Asia Pacific (Singapore)',
        'ap-southeast-2': 'Asia Pacific (Sydney)',
        'ap-northeast-1': 'Asia Pacific (Tokyo)',
        'ap-south-1': 'Asia Pacific (Mumbai)',
        'sa-east-1': 'South America (Sao Paulo)',
    }
    
    def __init__(self):
        """Initialize AWS Pricing client - Uses IAM role or credentials"""
        # boto3 automatically uses IAM role if available, falls back to credentials
        self.pricing_client = boto3.client('pricing', region_name='us-east-1')
        self.enabled = True
        print("✅ AWS Pricing API initialized (using IAM role or credentials)")
    
    @lru_cache(maxsize=1000)
    def get_ec2_price(self, instance_type: str, region: str = 'us-east-1') -> float:
        """Get EC2 instance hourly price from AWS Pricing API"""
        if not instance_type:
            raise ValueError("instance_type is required")
        
        location = self.REGION_MAP.get(region, 'US East (N. Virginia)')
        
        response = self.pricing_client.get_products(
            ServiceCode='AmazonEC2',
            Filters=[
                {'Type': 'TERM_MATCH', 'Field': 'instanceType', 'Value': instance_type},
                {'Type': 'TERM_MATCH', 'Field': 'location', 'Value': location},
                {'Type': 'TERM_MATCH', 'Field': 'operatingSystem', 'Value': 'Linux'},
                {'Type': 'TERM_MATCH', 'Field': 'tenancy', 'Value': 'Shared'},
                {'Type': 'TERM_MATCH', 'Field': 'preInstalledSw', 'Value': 'NA'},
                {'Type': 'TERM_MATCH', 'Field': 'capacitystatus', 'Value': 'Used'}
            ],
            MaxResults=1
        )
        
        if not response['PriceList']:
            raise ValueError(f"No pricing found for {instance_type} in {region}")
        
        price_item = json.loads(response['PriceList'][0])
        on_demand = price_item['terms']['OnDemand']
        price_dimensions = list(on_demand.values())[0]['priceDimensions']
        hourly_price = float(list(price_dimensions.values())[0]['pricePerUnit']['USD'])
        
        return hourly_price
    
    @lru_cache(maxsize=1000)
    def get_rds_price(self, instance_class: str, engine: str = 'postgres', 
                      region: str = 'us-east-1') -> float:
        """Get RDS instance hourly price from AWS Pricing API"""
        if not instance_class:
            raise ValueError("instance_class is required")
        
        location = self.REGION_MAP.get(region, 'US East (N. Virginia)')
        
        engine_map = {
            'postgres': 'PostgreSQL',
            'mysql': 'MySQL',
            'mariadb': 'MariaDB',
            'oracle': 'Oracle',
            'sqlserver': 'SQL Server',
        }
        db_engine = engine_map.get(engine.lower(), 'PostgreSQL')
        
        response = self.pricing_client.get_products(
            ServiceCode='AmazonRDS',
            Filters=[
                {'Type': 'TERM_MATCH', 'Field': 'instanceType', 'Value': instance_class},
                {'Type': 'TERM_MATCH', 'Field': 'location', 'Value': location},
                {'Type': 'TERM_MATCH', 'Field': 'databaseEngine', 'Value': db_engine},
                {'Type': 'TERM_MATCH', 'Field': 'deploymentOption', 'Value': 'Single-AZ'}
            ],
            MaxResults=1
        )
        
        if not response['PriceList']:
            raise ValueError(f"No pricing found for {instance_class} in {region}")
        
        price_item = json.loads(response['PriceList'][0])
        on_demand = price_item['terms']['OnDemand']
        price_dimensions = list(on_demand.values())[0]['priceDimensions']
        hourly_price = float(list(price_dimensions.values())[0]['pricePerUnit']['USD'])
        
        return hourly_price
    
    @lru_cache(maxsize=100)
    def get_s3_price(self, region: str = 'us-east-1') -> float:
        """Get S3 storage price per GB from AWS Pricing API"""
        location = self.REGION_MAP.get(region, 'US East (N. Virginia)')
        
        response = self.pricing_client.get_products(
            ServiceCode='AmazonS3',
            Filters=[
                {'Type': 'TERM_MATCH', 'Field': 'location', 'Value': location},
                {'Type': 'TERM_MATCH', 'Field': 'storageClass', 'Value': 'General Purpose'},
            ],
            MaxResults=1
        )
        
        if not response['PriceList']:
            raise ValueError(f"No S3 pricing found for {region}")
        
        price_item = json.loads(response['PriceList'][0])
        on_demand = price_item['terms']['OnDemand']
        price_dimensions = list(on_demand.values())[0]['priceDimensions']
        price_per_gb = float(list(price_dimensions.values())[0]['pricePerUnit']['USD'])
        
        return price_per_gb
    
    @lru_cache(maxsize=100)
    def get_alb_price(self, region: str = 'us-east-1') -> float:
        """Get ALB hourly price from AWS Pricing API"""
        location = self.REGION_MAP.get(region, 'US East (N. Virginia)')
        
        response = self.pricing_client.get_products(
            ServiceCode='AWSELB',
            Filters=[
                {'Type': 'TERM_MATCH', 'Field': 'location', 'Value': location},
                {'Type': 'TERM_MATCH', 'Field': 'productFamily', 'Value': 'Load Balancer-Application'}
            ],
            MaxResults=1
        )
        
        if not response['PriceList']:
            raise ValueError(f"No ALB pricing found for {region}")
        
        price_item = json.loads(response['PriceList'][0])
        on_demand = price_item['terms']['OnDemand']
        price_dimensions = list(on_demand.values())[0]['priceDimensions']
        hourly_price = float(list(price_dimensions.values())[0]['pricePerUnit']['USD'])
        
        return hourly_price


def get_pricing_service():
    """Get AWS Pricing Service instance"""
    return AWSPricingService()
