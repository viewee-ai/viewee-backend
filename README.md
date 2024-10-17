### **Create and Activate a Virtual Environment**

On **Windows**:
```
python -m venv venv
.\venv\Scripts\activate
```

On **macOS/Linux**:
```
python3 -m venv venv
source venv/bin/activate
```

**Install Dependencies**
```
pip install -r requirements.txt
```

### **Running the Application**
```
uvicorn app.main:app --reload
```
