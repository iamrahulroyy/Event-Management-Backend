from fastapi.responses import JSONResponse



def error_handler(details, status_code):
    return JSONResponse(content={"status": "error", "details": details}, status_code=status_code)