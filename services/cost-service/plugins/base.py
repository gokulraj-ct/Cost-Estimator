"""
Base Plugin Interface for AWS Resource Pricing
All resource plugins must inherit from this base class
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional


class ResourcePlugin(ABC):
    """Base class for all AWS resource pricing plugins"""
    
    @property
    @abstractmethod
    def resource_type(self) -> str:
        """
        AWS resource type (e.g., 'aws_instance', 'aws_db_instance')
        Must match Terraform resource type
        """
        pass
    
    @property
    @abstractmethod
    def display_name(self) -> str:
        """Human-readable name (e.g., 'EC2 Instance', 'RDS Database')"""
        pass
    
    @property
    @abstractmethod
    def required_attributes(self) -> list:
        """List of required attributes for cost calculation"""
        pass
    
    @abstractmethod
    def calculate_cost(self, attributes: Dict[str, Any], region: str = 'us-east-1') -> float:
        """
        Calculate monthly cost for this resource
        
        Args:
            attributes: Resource attributes from Terraform
            region: AWS region
            
        Returns:
            Monthly cost in USD
            
        Raises:
            ValueError: If required attributes are missing
        """
        pass
    
    def validate_attributes(self, attributes: Dict[str, Any]) -> None:
        """
        Validate that all required attributes are present
        
        Raises:
            ValueError: If required attributes are missing
        """
        missing = [attr for attr in self.required_attributes if not attributes.get(attr)]
        if missing:
            raise ValueError(f"{self.display_name} missing required attributes: {', '.join(missing)}")
    
    def get_cost_breakdown(self, attributes: Dict[str, Any], region: str = 'us-east-1') -> Dict[str, Any]:
        """
        Get detailed cost breakdown
        
        Returns:
            Dict with cost components
        """
        total_cost = self.calculate_cost(attributes, region)
        return {
            'total': total_cost,
            'components': []
        }
