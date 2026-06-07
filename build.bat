@echo off
echo === AI 排版助手 - 打包 ===
echo.

echo [0/3] 生成图标...
python create_icon.py

echo [1/3] 安装依赖...
pip install -r requirements.txt
pip install pyinstaller pillow

echo.
echo [2/3] 打包桌面版...
pyinstaller --onefile --windowed --icon=icon.ico --name="AI排版助手" main.py

echo.
echo [3/3] 打包完成!
echo   桌面版: dist\AI排版助手.exe
echo   网页版: 运行 streamlit run app.py
echo.
pause
