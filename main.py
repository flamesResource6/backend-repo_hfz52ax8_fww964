import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
from bson import ObjectId

from database import db, create_document, get_documents
from schemas import User, Cylinder, Customer, Order, OrderItem, DeliveryTask

app = FastAPI(title="Gas Cylinder Management API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def read_root():
    return {"message": "Gas Cylinder Management Backend Running"}


@app.get("/test")
def test_database():
    response = {
        "backend": "✅ Running",
        "database": "❌ Not Available",
        "database_url": None,
        "database_name": None,
        "connection_status": "Not Connected",
        "collections": []
    }

    try:
        if db is not None:
            response["database"] = "✅ Available"
            response["database_url"] = "✅ Set" if os.getenv("DATABASE_URL") else "❌ Not Set"
            response["database_name"] = db.name
            response["connection_status"] = "Connected"
            try:
                collections = db.list_collection_names()
                response["collections"] = collections[:10]
                response["database"] = "✅ Connected & Working"
            except Exception as e:
                response["database"] = f"⚠️ Connected but Error: {str(e)[:50]}"
        else:
            response["database"] = "⚠️ Available but not initialized"
    except Exception as e:
        response["database"] = f"❌ Error: {str(e)[:50]}"

    return response


# ---------- Auth (Demo) ----------
class LoginRequest(BaseModel):
    email: str
    password: str


@app.post("/auth/login")
def login(req: LoginRequest):
    user = db["user"].find_one({"email": req.email, "password": req.password}) if db else None
    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    user["_id"] = str(user["_id"])  # serialize
    return {"token": str(user["_id"]), "user": user}


# ---------- Inventory ----------
@app.get("/inventory", response_model=List[Cylinder])
def list_inventory():
    docs = get_documents("cylinder") if db else []
    # convert bson to pydantic-like dicts
    result = []
    for d in docs:
        d.pop("_id", None)
        result.append(d)
    return result


@app.post("/inventory")
def add_cylinder(cyl: Cylinder):
    if db is None:
        raise HTTPException(status_code=500, detail="Database not available")
    # ensure unique barcode
    if db["cylinder"].find_one({"barcode": cyl.barcode}):
        raise HTTPException(status_code=400, detail="Barcode already exists")
    inserted_id = create_document("cylinder", cyl)
    return {"id": inserted_id}


# ---------- Customers ----------
@app.post("/customers")
def create_customer(c: Customer):
    if db is None:
        raise HTTPException(status_code=500, detail="Database not available")
    cid = create_document("customer", c)
    return {"id": cid}


@app.get("/customers")
def list_customers():
    docs = get_documents("customer") if db else []
    for d in docs:
        d["_id"] = str(d["_id"]) if d.get("_id") else None
    return docs


# ---------- Orders ----------
class CreateOrderRequest(BaseModel):
    customer_id: str
    items: List[OrderItem]


@app.post("/orders")
def create_order(req: CreateOrderRequest):
    if db is None:
        raise HTTPException(status_code=500, detail="Database not available")
    order = Order(customer_id=req.customer_id, items=req.items)
    oid = create_document("order", order)
    return {"id": oid}


@app.get("/orders")
def list_orders(status: Optional[str] = None):
    filt = {"status": status} if status else {}
    docs = get_documents("order", filt)
    for d in docs:
        d["_id"] = str(d["_id"]) if d.get("_id") else None
    return docs


# ---------- Delivery Tasks ----------
@app.post("/deliveries")
def create_delivery(task: DeliveryTask):
    if db is None:
        raise HTTPException(status_code=500, detail="Database not available")
    tid = create_document("deliverytask", task)
    return {"id": tid}


@app.get("/deliveries")
def list_deliveries(status: Optional[str] = None):
    filt = {"status": status} if status else {}
    docs = get_documents("deliverytask", filt)
    for d in docs:
        d["_id"] = str(d["_id"]) if d.get("_id") else None
    return docs


# ---------- Schema exposure (for viewer tools) ----------
@app.get("/schema")
def get_schema_defs():
    return {
        "user": User.model_json_schema(),
        "cylinder": Cylinder.model_json_schema(),
        "customer": Customer.model_json_schema(),
        "order": Order.model_json_schema(),
        "deliverytask": DeliveryTask.model_json_schema(),
    }


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
