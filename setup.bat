@echo off
echo ===================================
echo Cai dat Blog Application
echo ===================================

:: Kiem tra Python da duoc cai dat chua
python --version > nul 2>&1
if %errorlevel% neq 0 (
    echo Python chua duoc cai dat. Vui long cai dat Python tai python.org
    exit /b 1
)

:: Tao moi truong ao
echo Dang tao moi truong ao...
if exist .venv (
    echo Moi truong ao da ton tai. Xoa va tao lai? (Y/N)
    set /p delenv=
    if /I "%delenv%"=="Y" (
        echo Dang xoa moi truong cu...
        rmdir /s /q .venv
        python -m venv .venv
    )
) else (
    python -m venv .venv
)

:: Kich hoat moi truong ao
echo Dang kich hoat moi truong ao...
call .venv\Scripts\activate.bat

:: Cai dat cac goi can thiet
echo Dang cai dat cac goi...
pip install flask flask-sqlalchemy flask-login

:: Tao thu muc cho ung dung
if not exist my_blog (
    mkdir my_blog
    mkdir my_blog\templates
    mkdir my_blog\static
    echo Tao cac thu muc ung dung thanh cong
)


echo ===================================
echo Cai dat hoan tat!
echo ===================================
echo Huong dan su dung:
echo 1. Kich hoat moi truong ao: .venv\Scripts\activate
echo 2. Chay ung dung: python my_blog/app.py
echo 3. Mo trinh duyet va truy cap: http://127.0.0.1:5000
echo 4. Tai khoan admin mac dinh:
echo    - Email: admin@example.com
echo    - Mat khau: admin123
echo ===================================

pause