package main

import (
	"log"
	"net/http"
	"regexp"
	"strings"

	"github.com/gin-gonic/gin"
)

// Resource represents a parsed Terraform resource
type Resource struct {
	Type       string                 `json:"type"`
	Name       string                 `json:"name"`
	Attributes map[string]interface{} `json:"attributes"`
	Region     string                 `json:"region"`
}

// ParseRequest represents the API request
type ParseRequest struct {
	Files []struct {
		Name    string `json:"name"`
		Content string `json:"content"`
	} `json:"files"`
	Region string `json:"region"`
}

// ParseResponse represents the API response
type ParseResponse struct {
	Resources []Resource `json:"resources"`
	Count     int        `json:"count"`
}

// SimpleTerraformParser handles basic Terraform parsing
type SimpleTerraformParser struct{}

// ParseContent parses Terraform content using regex (simplified for prototype)
func (p *SimpleTerraformParser) ParseContent(content string, defaultRegion string) []Resource {
	resources := []Resource{}
	
	// Extract region from provider block
	region := defaultRegion
	if region == "" {
		region = "us-east-1"
	}
	
	providerRegex := regexp.MustCompile(`provider\s+"aws"\s*\{([^}]*)\}`)
	providerMatch := providerRegex.FindStringSubmatch(content)
	if len(providerMatch) >= 2 {
		providerBody := providerMatch[1]
		regionRegex := regexp.MustCompile(`region\s*=\s*"([^"]+)"`)
		regionMatch := regionRegex.FindStringSubmatch(providerBody)
		if len(regionMatch) >= 2 {
			region = regionMatch[1]
		}
	}
	
	// Regex to match resource blocks
	resourceRegex := regexp.MustCompile(`resource\s+"([^"]+)"\s+"([^"]+)"\s*\{([^}]*)\}`)
	matches := resourceRegex.FindAllStringSubmatch(content, -1)
	
	for _, match := range matches {
		if len(match) >= 4 {
			resourceType := match[1]
			resourceName := match[2]
			body := match[3]
			
			// Only process AWS resources
			if strings.HasPrefix(resourceType, "aws_") {
				attrs := parseAttributes(body)
				
				resources = append(resources, Resource{
					Type:       resourceType,
					Name:       resourceName,
					Attributes: attrs,
					Region:     region,
				})
			}
		}
	}
	
	return resources
}

// parseAttributes extracts simple key-value pairs
func parseAttributes(body string) map[string]interface{} {
	attrs := make(map[string]interface{})
	
	// Match simple attributes like: instance_type = "t3.medium"
	attrRegex := regexp.MustCompile(`(\w+)\s*=\s*"([^"]+)"`)
	matches := attrRegex.FindAllStringSubmatch(body, -1)
	
	for _, match := range matches {
		if len(match) >= 3 {
			key := match[1]
			value := match[2]
			attrs[key] = value
		}
	}
	
	// Match numeric attributes like: allocated_storage = 100
	numRegex := regexp.MustCompile(`(\w+)\s*=\s*(\d+)`)
	numMatches := numRegex.FindAllStringSubmatch(body, -1)
	
	for _, match := range numMatches {
		if len(match) >= 3 {
			key := match[1]
			value := match[2]
			attrs[key] = value
		}
	}
	
	return attrs
}

func main() {
	router := gin.Default()
	parser := &SimpleTerraformParser{}

	// Health check
	router.GET("/health", func(c *gin.Context) {
		c.JSON(http.StatusOK, gin.H{
			"status":  "healthy",
			"service": "parser-service",
		})
	})

	// Parse endpoint
	router.POST("/api/v1/parse", func(c *gin.Context) {
		var req ParseRequest
		if err := c.BindJSON(&req); err != nil {
			c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
			return
		}

		allResources := []Resource{}
		
		for _, file := range req.Files {
			resources := parser.ParseContent(file.Content, req.Region)
			allResources = append(allResources, resources...)
		}

		c.JSON(http.StatusOK, ParseResponse{
			Resources: allResources,
			Count:     len(allResources),
		})
	})

	log.Println("🚀 Parser Service starting on :8001")
	router.Run(":8001")
}
