### **Create and Activate a Virtual Environment**

1. Create the virtual environment (if you haven't already):

On **Windows**:

```
python -m venv venv
```

On **macOS/Linux**:

```
python3 -m venv venv
```

2. Activate the virtual environment:
   On **Windows**:

```
.\venv\Scripts\activate
```

On **macOS/Linux**:

```
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

### In Case of SSL Error (MacOS)

```
sudo /Applications/Python\ 3.10/Install\ Certificates.command
```
