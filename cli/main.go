package main

import (
	"bytes"
	"encoding/json"
	"fmt"
	"io/ioutil"
	"net/http"
	"os"
	"path/filepath"
	"strings"

	"github.com/olekukonko/tablewriter"
	"github.com/spf13/cobra"
)

const (
	apiURL = "http://localhost:8000"
)

type FileContent struct {
	Name    string `json:"name"`
	Content string `json:"content"`
}

type EstimateRequest struct {
	Files  []FileContent `json:"files"`
	Region string        `json:"region"`
}

type EstimateResponse struct {
	EstimateID       string  `json:"estimate_id"`
	TotalMonthlyCost float64 `json:"total_monthly_cost"`
	Currency         string  `json:"currency"`
	Region           string  `json:"region"`
	ResourceCount    int     `json:"resource_count"`
	Breakdown        []struct {
		Resource    string  `json:"resource"`
		Type        string  `json:"type"`
		MonthlyCost float64 `json:"monthly_cost"`
	} `json:"breakdown"`
}

var (
	path      string
	region    string
	format    string
	breakdown bool
)

var rootCmd = &cobra.Command{
	Use:   "kostructure",
	Short: "Kostructure - AWS Infrastructure Cost Estimator",
	Long:  `Analyze Terraform files and estimate AWS infrastructure costs`,
}

var estimateCmd = &cobra.Command{
	Use:   "estimate",
	Short: "Estimate infrastructure costs",
	Run:   runEstimate,
}

func init() {
	estimateCmd.Flags().StringVarP(&path, "path", "p", ".", "Path to Terraform files")
	estimateCmd.Flags().StringVarP(&region, "region", "r", "us-east-1", "AWS region")
	estimateCmd.Flags().StringVarP(&format, "format", "f", "table", "Output format (table, json)")
	estimateCmd.Flags().BoolVarP(&breakdown, "breakdown", "b", true, "Show detailed breakdown")
	
	rootCmd.AddCommand(estimateCmd)
}

func runEstimate(cmd *cobra.Command, args []string) {
	// Read Terraform files
	files, err := readTerraformFiles(path)
	if err != nil {
		fmt.Printf("Error reading files: %v\n", err)
		os.Exit(1)
	}

	if len(files) == 0 {
		fmt.Println("No Terraform files found")
		os.Exit(1)
	}

	fmt.Printf("📁 Found %d Terraform file(s)\n", len(files))
	fmt.Println("💰 Calculating costs...")

	// Call API (don't send region, let parser extract from provider block)
	req := EstimateRequest{
		Files:  files,
		Region: "", // Empty - parser will extract from provider block
	}

	jsonData, _ := json.Marshal(req)
	resp, err := http.Post(apiURL+"/api/v1/estimate", "application/json", bytes.NewBuffer(jsonData))
	if err != nil {
		fmt.Printf("Error calling API: %v\n", err)
		os.Exit(1)
	}
	defer resp.Body.Close()

	body, _ := ioutil.ReadAll(resp.Body)
	
	var result EstimateResponse
	if err := json.Unmarshal(body, &result); err != nil {
		fmt.Printf("Error parsing response: %v\n", err)
		os.Exit(1)
	}

	// Display results
	if format == "json" {
		fmt.Println(string(body))
	} else {
		displayTable(result)
	}
}

func readTerraformFiles(dir string) ([]FileContent, error) {
	var files []FileContent

	err := filepath.Walk(dir, func(path string, info os.FileInfo, err error) error {
		if err != nil {
			return err
		}

		if !info.IsDir() && strings.HasSuffix(info.Name(), ".tf") {
			content, err := ioutil.ReadFile(path)
			if err != nil {
				return err
			}

			files = append(files, FileContent{
				Name:    info.Name(),
				Content: string(content),
			})
		}

		return nil
	})

	return files, err
}

func displayTable(result EstimateResponse) {
	fmt.Println("\n" + strings.Repeat("=", 60))
	fmt.Printf("💰 Total Monthly Cost: $%.2f %s\n", result.TotalMonthlyCost, result.Currency)
	fmt.Printf("📍 Region: %s\n", result.Region)
	fmt.Printf("📦 Resources: %d\n", result.ResourceCount)
	fmt.Printf("🆔 Estimate ID: %s\n", result.EstimateID)
	fmt.Println(strings.Repeat("=", 60))

	if breakdown && len(result.Breakdown) > 0 {
		fmt.Println("\n📊 Cost Breakdown:")
		
		table := tablewriter.NewWriter(os.Stdout)
		table.SetHeader([]string{"Resource", "Type", "Monthly Cost"})
		table.SetBorder(true)

		for _, item := range result.Breakdown {
			table.Append([]string{
				item.Resource,
				item.Type,
				fmt.Sprintf("$%.2f", item.MonthlyCost),
			})
		}

		table.Render()
	}

	fmt.Println()
}

func main() {
	if err := rootCmd.Execute(); err != nil {
		fmt.Println(err)
		os.Exit(1)
	}
}
