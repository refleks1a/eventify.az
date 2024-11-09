<div align='center'>

<h1>eventify.az</h1>
<p>Full stack web application built by refleks1a. The application, where agents can sell and clients can buy real estate. </p>

<h4> <span> · </span> <a href="https://github.com/refleks1a/eventify.az/blob/master/README.md"> Documentation </a> <span> · </span> <a href="https://github.com/refleks1a/eventify.az/issues"> Report Bug </a> <span> · </span> <a href="https://github.com/refleks1a/eventify.az/issues"> Request Feature </a> </h4>


</div>

# :notebook_with_decorative_cover: Table of Contents

- [About the Project](#star2-about-the-project)
- [Contact](#handshake-contact)


## :star2: About the Project
### :space_invader: Tech Stack
<details> <summary>Client</summary> <ul>
<li><a href="">Js</a></li>
<li><a href="">HTML</a></li>
<li><a href="">CSS & SCSS</a></li>
</ul> </details>
<details> <summary>Server</summary> <ul>
<li><a href="">Python</a></li>
<li><a href="">FastAPI</a></li>
</ul> </details>
<details> <summary>Database</summary> <ul>
<li><a href="">MySQL</a></li>
<li><a href="">Redis</a></li>
</ul> </details>

## :toolbox: Getting Started

### :bangbang: Prerequisites

You need MySQL db to run the application
First login to your mysql through cmd with this command
```bash
mysql -u <username> -p
```
Create eventifyaz database in mysql shell, using this command
```bash
CREATE DATABASE eventifyaz;
```

### :running: Run Locally

Clone the project
```bash
https://github.com/refleks1a/eventify.az
```

Create virtual environment  by running
```bash
python -m venv venv 
```

Activate virtual environment by running
```bash
source venv/bin/activate (for MacOS) 
source venv/Scripts/activate (for Windows)
```

Install the requirements by running
(If using windows os, delete "uvloop==0.19.0" from requirements.txt)
```bash
pip install -r requirements.txt
```

Create .env file and fill it using .env_example as a reference

Go to API folder by running
```bash
cd API
```

Start API by running
```bash
uvicorn main:app --reload --proxy-headers --host 0.0.0.0 --port 8000
```

## :handshake: Contact

Agshin kerimov - [@linkedin_handle](https://www.linkedin.com/in/kerimovagshin) - kerimovaksin808@gmail.com

Project Link: [https://github.com/refleks1a/eventify.az]