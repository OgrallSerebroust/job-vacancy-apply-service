<h3 align="center">
    Job vacancy apply service
</h3>
<div align="center">
    Web service created for vacancy applying automation.
</div>

---

<div align="center">
    <img src="https://img.shields.io/badge/license-PolyForm Noncommercial-orange?labelColor=555555&color=007EC6" alt="License">
    <img alt="Dynamic TOML Badge" src="https://img.shields.io/badge/dynamic/toml?url=https://raw.githubusercontent.com/OgrallSerebroust/job-vacancy-apply-service/refs/heads/master/pyproject.toml&query=$.[project][version]&label=version&labelColor=555555&color=007EC6">
    <img alt="GitHub contributors" src="https://img.shields.io/github/contributors/OgrallSerebroust/job-vacancy-apply-service?labelColor=555555&color=007EC6">
    <img alt="GitHub forks" src="https://img.shields.io/github/forks/OgrallSerebroust/job-vacancy-apply-service?labelColor=555555&color=007EC6">
    <img alt="GitHub Repo stars" src="https://img.shields.io/github/stars/OgrallSerebroust/job-vacancy-apply-service?labelColor=555555&color=007EC6">
    <img alt="GitHub Issues" src="https://img.shields.io/github/issues/OgrallSerebroust/job-vacancy-apply-service?labelColor=555555&color=007EC6">
    <img alt="GitHub Pull Requests" src="https://img.shields.io/github/issues-pr/OgrallSerebroust/job-vacancy-apply-service?labelColor=555555&color=007EC6">
</div>

<details>
    <summary>
        <strong>
            Table of Contents :bookmark_tabs:
        </strong>
    </summary>

- [Features :muscle:](#features-muscle)
- [Getting Started :seedling:](#getting-started-seedling)
  - [Prerequisites :page\_with\_curl:](#prerequisites-page_with_curl)
  - [Installation :inbox\_tray:](#installation-inbox_tray)
- [Demo :mag::computer:](#demo-magcomputer)
- [Built With :wrench:](#built-with-wrench)

</details>

## Features :muscle:

* **Applying automation:** Service applies job offers automatically. All you need is tell about yourself and authorized to recruiting services by own.
* **Scalable recruting services support:** The service currently supports **hh.ru**. But in the future it'll support other recruitimg services, for example **Хабр Карьера** or **NoFluffJobs**. 
* **Stealth:** Thankfully to **playwright-stealth** service can operate via the browser like a human - with own browsing profile, and full tls-handshake.
* **Human behavior emulation:** For mimicring to a human and avoiding of anti-bot systems, in addition to stealth functionality, service has human behavior layer. For example, if new page is open, service makes human-like mouse movements uses besier-curves.
* **AI-generated cover letters:** If it's neccesary, service can generate meaningfull cover letter. All you need is tell about yourself, and your capabilities using example file. After it, service will use that information, also like vacancy page data, witch will be extract automaticly, to generate brilliant cover letter to current position.
* **Logging:** Service logging both its status and the results of work on each vacancy. In the future results will be accessible via GUI.


## Getting Started :seedling:

If you want to check that project you can easily setup it on your own machine. Just check prerequisites and follow steps below.

### Prerequisites :page_with_curl:

Before you begin, ensure you have the following installed on your machine:

- **Ollama**
- **gemma3:4b**

> [!IMPORTANT]
> Therefore project uses local installed model you must ensure that your machine can provide at least 3.3 GB VRAM memory to proper work.

### Installation :inbox_tray:

To setup the project, follow these steps:

1. Clone this repository to your local machine:
   ```bash
    git clone https://github.com/OgrallSerebroust/job-vacancy-apply-service.git
    ```
2. Navigate to the project directory:
    ```bash
    cd job-vacancy-apply-service
    ```
3. Install project requirements uses standard command:
   ```bash
   pip install -r requirements.txt
   ```
4. Create .env using .env.example;
5. Now add your hh.ru resume ID to .env in the field:
   ```bash
   HH_RESUME_ID=
   ```

> [!NOTE]
> If you want to use cover letter generation properly you must tell service about you and your capabilities. Please follow steps below to make it:

1. Copy file **user_data.example.md** from the /neural_network/prompts to the same path with **user_data.md** filename.
2. Fill it in simple design, guided by headers.

> [!IMPORTANT]
> Don't delete headers. There is example of header: ## KEY SKILS

## Demo :mag::computer:

You can find more in my business-card
<a href="https://stefplotva.ru/projects/">
  website
</a>. There will be real demonstrations here in the future.

> [!NOTE]
> Service state in stable, but early version. Also service was created in short time. If you spotted bug or just want to contribute it, don't remember that service version will be updated soon.

## Built With :wrench:

[![Python](https://img.shields.io/badge/Python-FFD43B?style=for-the-badge&logo=python&logoColor=blue)](#)
[![Pydantic](https://img.shields.io/badge/Pydantic-E92063?style=for-the-badge&logo=Pydantic&logoColor=white)](#)
[![Playwright](https://img.shields.io/badge/Playwright-45ba4b?style=for-the-badge&logo=Playwright&logoColor=white)](#)
[![Ollama](https://img.shields.io/badge/ollama-000000?style=for-the-badge&logo=ollama&logoColor=white)](#)
[![Vulkan](https://img.shields.io/badge/vulkan-A41E22?style=for-the-badge&logo=vulkan&logoColor=white)](#)