#!/usr/bin/env python3
"""
간단한 FastAPI 테스트 서버
"""

from fastapi import FastAPI
import uvicorn

app = FastAPI(title="Test API Server")

@app.get("/")
async def root():
    return {"message": "✅ 테스트 서버 작동 중!", "status": "success"}

@app.get("/health")
async def health():
    return {"status": "healthy", "message": "테스트 서버 정상"}

if __name__ == "__main__":
    print("🚀 테스트 서버 시작...")
    print("📡 URL: http://localhost:8001")
    uvicorn.run(app, host="0.0.0.0", port=8001, log_level="info") 