# 🚀 How to Add Changes

Follow these simple steps to add updates safely.

---

### 1️⃣ Checkout from `staging`
```bash
git checkout staging
git pull origin staging
git checkout -b <feature-branch-name>
```

---

### 2️⃣ Make and Stage Changes
```bash
# edit your files
git add .
git commit -m "feat: <short description>"
```

---

### 3️⃣ Push Your Branch
```bash
git push origin <feature-branch-name>
```

---

### 4️⃣ Create a Pull Request
- Go to GitHub  
- **Base branch:** `staging`  
- **Compare branch:** your `<feature-branch-name>`  
- Add a clear title & short description  
- Submit the PR for review

---

### ⚠️ Notes
- Never push directly to `main` or `staging`.  
- Always branch off from `staging`.  
- Keep commits atomic and messages meaningful.
