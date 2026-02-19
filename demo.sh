#!/bin/bash
#
# Interactive Demo Script - Try these commands to learn netdiag
#

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

API_URL="http://localhost:5001"

demo_header() {
    echo -e "\n${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}\n"
}

demo_step() {
    echo -e "${YELLOW}→ $1${NC}"
}

demo_success() {
    echo -e "${GREEN}✓ $1${NC}\n"
}

demo_code() {
    echo -e "${BLUE}$${NC} $1\n"
}

# Check if service is running
check_service() {
    if ! curl -s "$API_URL/health" > /dev/null 2>&1; then
        echo -e "${RED}Error: Service not running at $API_URL${NC}"
        echo -e "Start it with: ${YELLOW}cd netdiag-service && docker compose up -d${NC}"
        exit 1
    fi
}

demo_1_health() {
    demo_header "Demo 1: Check Service Health"
    
    demo_step "Check if netdiag service is running"
    demo_code "curl http://localhost:5001/health"
    
    curl -s "$API_URL/health" | jq .
    demo_success "Service is healthy"
}

demo_2_scan() {
    demo_header "Demo 2: Run a Network Scan"
    
    demo_step "Scan multiple hosts at once"
    demo_code "./netdiag scan 8.8.8.8,1.1.1.1"
    
    ./netdiag scan 8.8.8.8,1.1.1.1
    demo_success "Scan completed"
}

demo_3_results() {
    demo_header "Demo 3: View Latest Results"
    
    demo_step "Show results from last scan"
    demo_code "./netdiag results"
    
    ./netdiag results | jq '.results | to_entries[] | {host: .key, status: .value.status, latency: .value.avg_ms, loss: .value.packet_loss_pct}'
    demo_success "Results displayed"
}

demo_4_host_results() {
    demo_header "Demo 4: Get Results for Specific Host"
    
    demo_step "View detailed info for 8.8.8.8"
    demo_code "./netdiag results 8.8.8.8"
    
    ./netdiag results 8.8.8.8
    demo_success "Host results retrieved"
}

demo_5_config() {
    demo_header "Demo 5: View Configuration"
    
    demo_step "Show current configuration"
    demo_code "./netdiag config"
    
    ./netdiag config | jq .
    demo_success "Configuration displayed"
}

demo_6_history() {
    demo_header "Demo 6: View Historical Data"
    
    demo_step "Get measurements from last 1 hour for 8.8.8.8"
    demo_code "./netdiag history 8.8.8.8 1"
    
    HISTORY=$(./netdiag history 8.8.8.8 1 | jq '.history | length')
    echo "Found $HISTORY measurements in last hour"
    
    ./netdiag history 8.8.8.8 1 | jq '.history[0:3] | .[] | {timestamp: .timestamp, status: .status, latency: .avg_ms}' 2>/dev/null || echo "No history yet (service just started)"
    demo_success "Historical data retrieved"
}

demo_7_api() {
    demo_header "Demo 7: REST API - Direct Scan"
    
    demo_step "Use curl to POST a scan request"
    demo_code "curl -X POST http://localhost:5001/api/scan -d '{\"targets\": [\"8.8.8.8\"]}"
    
    curl -s -X POST "$API_URL/api/scan" \
      -H "Content-Type: application/json" \
      -d '{"targets": ["8.8.8.8"]}' | jq '.results.["8.8.8.8"] | {status, avg_ms, packet_loss_pct}'
    
    demo_success "API scan executed"
}

demo_8_monitoring() {
    demo_header "Demo 8: Continuous Monitoring (background)"
    
    demo_step "The service automatically scans every 60 seconds"
    demo_code "docker compose logs -f netdiag-service | grep -E 'scan|ALERT'"
    
    echo -e "${YELLOW}(Service is scanning in background. Press Ctrl+C to continue...)${NC}"
    echo "Next scan happens automatically. You can:"
    echo "  - Watch logs: docker compose logs -f netdiag-service"
    echo "  - Get results: ./netdiag results"
    echo "  - Check history: ./netdiag history <host> <hours>"
}

demo_9_alerts() {
    demo_header "Demo 9: Alert Configuration"
    
    demo_step "Current alert thresholds:"
    demo_code "./netdiag config"
    ./netdiag config | jq '{alert_loss_threshold_pct, alert_latency_threshold_ms}'
    
    echo -e "\n${YELLOW}To trigger alerts on very small changes:${NC}"
    demo_code "./netdiag config set alert_latency_threshold_ms 5"
    
    echo -e "\n${YELLOW}Then watch logs for alerts:${NC}"
    demo_code "docker compose logs -f netdiag-service | grep ALERT"
}

demo_10_summary() {
    demo_header "Summary - What You Can Do"
    
    cat << 'EOF'
✓ Health Checks       : ./netdiag health
✓ On-Demand Scans     : ./netdiag scan 8.8.8.8,1.1.1.1
✓ View Results        : ./netdiag results [host]
✓ Historical Data     : ./netdiag history <host> <hours>
✓ Configuration       : ./netdiag config [set <key> <value>]
✓ REST API            : curl http://localhost:5001/api/*
✓ Logs & Monitoring   : docker compose logs -f netdiag-service
✓ Python Client       : from netdiag_client import NetDiagClient

Next Steps:
1. Set up your hosts to monitor (edit config/netdiag.json)
2. Restart service: docker compose restart netdiag-service
3. Watch for alerts: docker compose logs -f netdiag-service | grep ALERT
4. Integrate with your monitoring: Use Python client or REST API
EOF
}

# Main menu
main_menu() {
    clear
    demo_header "Network Diagnostics Service - Interactive Demo"
    
    echo "Choose a demo to run:"
    echo ""
    echo "  1) Health Check"
    echo "  2) Run a Network Scan"
    echo "  3) View Latest Results"
    echo "  4) Get Specific Host Results"
    echo "  5) View Configuration"
    echo "  6) View Historical Data"
    echo "  7) REST API Direct Scan"
    echo "  8) Background Monitoring"
    echo "  9) Alert Configuration"
    echo "  10) Summary & Next Steps"
    echo "  0) Exit"
    echo ""
    read -p "Enter choice [0-10]: " choice
    
    case $choice in
        1) demo_1_health ;;
        2) demo_2_scan ;;
        3) demo_3_results ;;
        4) demo_4_host_results ;;
        5) demo_5_config ;;
        6) demo_6_history ;;
        7) demo_7_api ;;
        8) demo_8_monitoring ;;
        9) demo_9_alerts ;;
        10) demo_10_summary ;;
        0) echo "Goodbye!"; exit 0 ;;
        *) echo "Invalid choice"; sleep 1 ;;
    esac
    
    read -p "Press Enter to continue..." dummy
    main_menu
}

# Run all demos automatically
run_all() {
    demo_1_health
    read -p "Press Enter to continue..." dummy
    
    demo_2_scan
    read -p "Press Enter to continue..." dummy
    
    demo_3_results
    read -p "Press Enter to continue..." dummy
    
    demo_5_config
    read -p "Press Enter to continue..." dummy
    
    demo_10_summary
}

# Main
check_service

if [ "$1" == "--all" ]; then
    run_all
elif [ "$1" == "--demo" ] && [ -n "$2" ]; then
    demo_$2
else
    main_menu
fi
