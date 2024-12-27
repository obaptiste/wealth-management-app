# <span style="color:#3498db;">Wealth Management App</span>

A modern, containerized web application that provides tools for personal or business finance management. It leverages <span style="color:#e67e22;">**FastAPI**</span> for the backend (including some sentiment analysis features!) and a <span style="color:#9b59b6;">**Next.js**</span> admin dashboard for managing customers, invoices, and more.

---

## <span style="color:#e74c3c;">Table of Contents</span>

1. [<span style="color:#27ae60;">Overview</span>](#overview)  
2. [<span style="color:#f1c40f;">Features</span>](#features)  
3. [<span style="color:#16a085;">Tech Stack</span>](#tech-stack)  
4. [Getting Started](#getting-started)  
5. [Setup and Installation](#setup-and-installation)  
6. [Running Locally](#running-locally)  
7. [Using Docker](#using-docker)  
8. [Folder Structure](#folder-structure)  
9. [Contributing](#contributing)  
10. [License](#license)

---

## Overview

This project aims to provide a streamlined platform for analyzing financial data, managing portfolios, and offering an invoice/customer management dashboard. Whether you’re tracking personal stock holdings or supporting your small business, the Wealth Management App is designed to help you stay on top of your finances.

---

## <span style="color:#e67e22;">Features</span>

1. **User Authentication**  
   - Secure user registration, login, and token-based auth using **FastAPI**, **OAuth2**, and **JWT** tokens.

2. **Portfolio Management**  
   - Create, update, and view personal or business portfolios.  
   - Integrates with [YFinance](https://pypi.org/project/yfinance/) to fetch real-time stock data.

3. **Sentiment Analysis**  
   - Uses <span style="color:#9b59b6;">Hugging Face Transformers</span> (FinBERT) to gauge the sentiment of financial news or text input.  
   - Includes potential integration with social media sentiment (Twitter).

4. **Admin Dashboard**  
   - Built with **Next.js** for displaying and managing users, invoices, and more.  
   - A responsive UI so you can manage invoices on desktop or mobile.

5. **Database Migrations**  
   - Uses **Alembic** for seamless schema changes on the backend.

---

## <span style="color:#2ecc71;">Tech Stack</span>

- **Backend**: [FastAPI](https://fastapi.tiangolo.com/)  
- **Database**: [SQLAlchemy](https://www.sqlalchemy.org/) + Alembic migrations  
- **Authentication**: OAuth2 + JWT  
- **ML/AI**: [Hugging Face Transformers](https://github.com/huggingface/transformers) (FinBERT model)  
- **Frontend**: [Next.js](https://nextjs.org/) admin dashboard (with React)  
- **Deployment**: Dockerized environment

