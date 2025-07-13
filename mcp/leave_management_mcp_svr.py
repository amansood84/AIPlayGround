from fastmcp import FastMCP
from typing import Dict, Any
from pathlib import Path

# =============================================================================
#  Leave Management System (LMS) - Core Logic
# =============================================================================
#  This is a simplified, in-memory implementation of the leave management
#  system.  In a real-world application, you would replace this with
#  database interactions, business logic, and integration with your
#  existing HR systems.
#
#  The purpose of this class is to define the core functions of the
#  leave management system, which will then be exposed through the MCP
#  server.
#

"""
Initializes the leave management system.
"""
leave_data = {
    1001: {"name": "Alice Smith", "leave_balance": 15, "leaves_taken": ["2025-01-01", "2025-02-14"]},
    1002: {"name": "Bob Johnson", "leave_balance": 10, "leaves_taken": ["2025-01-04"]},
    1003: {"name": "Charlie Brown", "leave_balance": 20, "leaves_taken": ["2025-04-01", "2025-05-05"]},
}

# =============================================================================
#  MCP Server Implementation
# =============================================================================

# Create an MCP server for HTTP/SSE
#https://github.com/modelcontextprotocol/python-sdk/issues/808
#mcp = FastMCP("Leave Mgmt Server", stateless_http=True)

# Create an MCP server listening on stdio 
mcp = FastMCP("Leave Mgmt Server", host="192.168.101.2", port=9000)

@mcp.tool()
def get_employee_leave_balance(employee_id: str) -> Dict[str, Any]:
    """
    Gets the leave balance for an employee.

    Args:
        employee_id: The ID of the employee or all to return balance for all employees.

    Returns:
        A dictionary containing the employee's name and leave balance,
        or an error message if the employee is not found.
    """
 
    if employee_id == "all":
        leave_balances = {}
        # Iterate through the original dictionary
        for e_id, data in leave_data.items():
            # Extract the 'leave_balance' for each employee
            leave_balances[e_id] = data['leave_balance']

        return {"status": "success", "leave_balances_all": leave_balances}
    e_id = int (employee_id)
    if e_id not in leave_data:
        return {"status": "error", "reason": "employee not found"}
    employee = leave_data[e_id]
    return {"status": "success", "leave_balance": employee["leave_balance"]}

@mcp.tool()
def get_employee_leaves_taken(employee_id: str) -> Dict[str, Any]:
    """
    Gets the dates for which employee has taken the leaves

    Args:
        employee_id: The ID of the employee or all to return leaves taken by all employees.

    Returns:
        A dictionary containing the employee's name and and array of dates on which leaves were taken
        or an error message if the employee is not found.
    """

    if employee_id == "all":
        leave_taken = {}
        # Iterate through the original dictionary
        for e_id, data in leave_data.items():
            # Extract the 'leave_taken' for each employee
            leave_taken[e_id] = data['leaves_taken']

        return {"status": "success", "leave_taken_all": leave_taken}
    e_id = int (employee_id)
    if e_id not in leave_data:
        return {"status": "error", "reason": "employee not found"}
    employee = leave_data[e_id]
    return {"status": "success", "leaves_taken": employee["leaves_taken"]}

@mcp.resource("resource://get_system_prompt")
def get_system_prompt() -> Dict[str, Any]:
    """
    Reads the contents of the file for the system prompt

    Args:
        None

    Returns:
        System Prompt of the agent

    """
    file_path = Path("./documents/system_prompt.txt")
    return {"status": "success", "content": file_path.read_text()}

# =============================================================================
#  Main Function
# =============================================================================
if __name__ == "__main__":
    mcp.run(transport="streamable-http") 
    mcp.run() 
