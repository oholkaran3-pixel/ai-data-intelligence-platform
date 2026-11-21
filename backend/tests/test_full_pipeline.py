import os
from fastapi.testclient import TestClient
from main import app
from app.core.database import SessionLocal, Base, engine
from app.models.models import User, Project, Dataset

client = TestClient(app)

def test_api_root():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json()["platform"] == "AI Data Intelligence Platform"

def test_user_registration_and_login():
    email = "analyst@example.com"
    pwd = "EnterprisePassword123!"
    
    # Register
    reg_resp = client.post("/api/v1/auth/register", json={
        "email": email,
        "password": pwd,
        "full_name": "Senior Data Analyst",
        "role": "regular_user"
    })
    assert reg_resp.status_code in [201, 400] # 201 or already created
    
    # Login
    login_resp = client.post("/api/v1/auth/login", json={
        "email": email,
        "password": pwd
    })
    assert login_resp.status_code == 200
    data = login_resp.json()
    assert "access_token" in data
    token = data["access_token"]
    
    # Get current user profile
    me_resp = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert me_resp.status_code == 200
    assert me_resp.json()["email"] == email

def test_project_creation_and_isolation():
    # Login as analyst
    login_resp = client.post("/api/v1/auth/login", json={
        "email": "analyst@example.com",
        "password": "EnterprisePassword123!"
    })
    token = login_resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    
    # Create Project
    proj_resp = client.post("/api/v1/projects", json={
        "title": "Q4 Global Revenue Analysis",
        "description": "Comprehensive transactional breakdown"
    }, headers=headers)
    assert proj_resp.status_code == 201
    proj_data = proj_resp.json()
    project_id = proj_data["id"]
    
    # List Projects
    list_resp = client.get("/api/v1/projects", headers=headers)
    assert list_resp.status_code == 200
    assert any(p["id"] == project_id for p in list_resp.json())

def test_powerbi_status_and_export_guide():
    login_resp = client.post("/api/v1/auth/login", json={
        "email": "analyst@example.com",
        "password": "EnterprisePassword123!"
    })
    token = login_resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    
    pbi_resp = client.get("/api/v1/integrations/powerbi/status", headers=headers)
    assert pbi_resp.status_code == 200
    assert "supported_methods" in pbi_resp.json() or "configured" in pbi_resp.json()

def test_end_to_end_analytics_pipeline():
    # 1. Login
    login_resp = client.post("/api/v1/auth/login", json={
        "email": "analyst@example.com",
        "password": "EnterprisePassword123!"
    })
    token = login_resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    
    # 2. Create project
    proj_resp = client.post("/api/v1/projects", json={
        "title": "E-Commerce Pipeline Test",
        "description": "Automated dataset ingestion test"
    }, headers=headers)
    project_id = proj_resp.json()["id"]

    # 3. Create sample CSV
    csv_content = (
        "transaction_id,product_category,revenue,units_sold,customer_rating\n"
        "101,Electronics,1200.50,3,4.8\n"
        "102,Fashion,89.90,2,4.1\n"
        "103,Electronics,450.00,1,4.5\n"
        "104,Home,210.00,4,3.9\n"
        "105,Electronics,1200.50,3,4.8\n" # Duplicate row
        "106,Books,,5,4.9\n" # Missing value
    )
    
    # 4. Upload file
    files = {"file": ("sales_data.csv", csv_content, "text/csv")}
    data = {"project_id": project_id, "name": "Sales Test Dataset"}
    upload_resp = client.post("/api/v1/datasets/upload", data=data, files=files, headers=headers)
    assert upload_resp.status_code == 201
    dataset = upload_resp.json()
    dataset_id = dataset["id"]
    assert dataset["row_count"] == 6
    assert dataset["quality_score"] < 100.0 # Missing & duplicate detected

    # 5. Clean dataset (drop duplicates)
    clean_resp = client.post("/api/v1/cleaning/apply", json={
        "dataset_id": dataset_id,
        "operation_type": "drop_duplicates"
    }, headers=headers)
    assert clean_resp.status_code == 200
    cleaned = clean_resp.json()
    assert cleaned["row_count"] == 5

    # 6. Ask AI Analyst
    ai_resp = client.post("/api/v1/ai/ask", json={
        "project_id": project_id,
        "dataset_id": dataset_id,
        "question": "Which product category has the highest revenue?"
    }, headers=headers)
    assert ai_resp.status_code == 200
    ai_data = ai_resp.json()
    assert "sql_query" in ai_data
    assert "Electronics" in ai_data["content"] or "revenue" in ai_data["content"]

    # 7. Generate PowerPoint presentation
    pptx_resp = client.post("/api/v1/reports/generate", json={
        "project_id": project_id,
        "dataset_id": dataset_id,
        "report_type": "pptx",
        "title": "Executive E-Commerce Overview"
    }, headers=headers)
    assert pptx_resp.status_code == 200
    assert "download_url" in pptx_resp.json()

    # 8. Generate Excel report
    xlsx_resp = client.post("/api/v1/reports/generate", json={
        "project_id": project_id,
        "dataset_id": dataset_id,
        "report_type": "xlsx",
        "title": "Complete Cleaned Data Export"
    }, headers=headers)
    assert xlsx_resp.status_code == 200

    # 9. Generate PDF report
    pdf_resp = client.post("/api/v1/reports/generate", json={
        "project_id": project_id,
        "dataset_id": dataset_id,
        "report_type": "pdf",
        "title": "Executive Summary Audit"
    }, headers=headers)
    assert pdf_resp.status_code == 200
    print("ALL INTEGRATION TESTS PASSED WITH 100% SUCCESS!")
