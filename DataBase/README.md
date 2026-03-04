# DataBase — Islamic Knowledge Source Files

This folder contains the PDF source documents that Al-Huda uses to build its vector knowledge base.

## What Goes Here

Place your Islamic source PDFs here:

- Sahih al-Bukhari (volumes 1–9)
- Sahih Muslim (volumes 1–7)
- Any other authentic Islamic texts in `.pdf`, `.docx`, or `.txt` format

## Supported Formats

| Format     | Extension       |
| ---------- | --------------- |
| PDF        | `.pdf`          |
| Word       | `.docx`, `.doc` |
| Plain Text | `.txt`          |

## How It Works

On startup, the app scans this folder and indexes all supported files into the FAISS vector database (`vector_db.pkl`). If you add new files, use the **Rescan Database** button in the app or call `POST /rescan-database`.

## Note on Git

PDF files are excluded from version control (`.gitignore`) because they are large binary files. When cloning this repository, you need to add your own PDF sources to this folder before the first run.
