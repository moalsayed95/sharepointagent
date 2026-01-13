# Security Guidelines

## 🔒 Critical Security Rules

### ⚠️ NEVER Commit These Files

The following files contain secrets and **MUST NEVER** be committed to git:

- `.env` - Contains all credentials and API keys
- `.env.*` - Any environment-specific config files
- `credentials.json` - Service account credentials
- `secrets.json` - Any JSON files with secrets
- `*.key`, `*.pem`, `*.pfx` - Certificate and key files
- `.azure/` - Azure CLI configuration

**These are already in `.gitignore`** - but double-check before pushing!

---

## ✅ What's Safe to Commit

These files are safe (secrets are replaced with placeholders):

- `.env.example` - Template with placeholder values
- `knowledge_sources.json` - Uses `${VAR_NAME}` placeholders
- All Python scripts - No hardcoded secrets
- Documentation files - No sensitive data

---

## 🛡️ Secret Management Best Practices

### 1. Use Environment Variables

All secrets are loaded from `.env`:

```python
from dotenv import load_dotenv
load_dotenv()

API_KEY = os.getenv("API_KEY")  # ✅ Good
API_KEY = "abc123xyz"            # ❌ Never do this
```

### 2. Verify Before Committing

Always check what you're about to commit:

```bash
# Check status
git status

# Check diff
git diff

# Verify .env is not listed
git ls-files | grep .env  # Should return nothing
```

### 3. Use .env.example as Template

When onboarding new team members:

```bash
cp .env.example .env
# Then fill in actual values in .env
```

### 4. Rotate Secrets Regularly

- **Service Principal secrets**: Every 6-12 months
- **API keys**: After team member departures
- **Connection strings**: After security incidents

---

## 🔍 How to Check for Accidentally Committed Secrets

### Check if .env was ever committed:

```bash
git log --all --full-history -- .env
```

If this returns anything, **the .env file was committed** and you need to:

1. Remove it from history (see below)
2. Rotate ALL secrets immediately
3. Notify security team

### Remove secrets from git history:

**If you accidentally committed secrets:**

```bash
# WARNING: This rewrites history - coordinate with team first!

# Remove .env from entire history
git filter-branch --force --index-filter \
  'git rm --cached --ignore-unmatch .env' \
  --prune-empty --tag-name-filter cat -- --all

# Force push (coordinate with team!)
git push origin --force --all
```

**Then immediately:**
1. Rotate all secrets that were exposed
2. Update `.env` with new secrets
3. Inform your security team

---

## 🚨 Incident Response

If secrets are accidentally pushed to GitHub:

### Immediate Actions (Within 15 minutes)

1. **Delete the commit/branch** if possible
2. **Rotate all exposed secrets immediately**:
   - Azure App Registration: Create new secret
   - Azure AI Search: Regenerate admin key
   - Azure AI Foundry: Regenerate project key
3. **Check for unauthorized access**:
   - Azure Portal → Activity Logs
   - Check for suspicious API calls

### Follow-up Actions (Within 24 hours)

1. **Investigate scope**:
   - How long were secrets exposed?
   - Who had access to the repository?
   - Any signs of unauthorized use?

2. **Update security measures**:
   - Review `.gitignore` completeness
   - Consider git hooks to prevent future incidents
   - Document lessons learned

3. **Notify stakeholders**:
   - Security team
   - Repository administrators
   - Affected service owners

---

## 🔐 Production Deployment

For production environments:

### Use Azure Key Vault

Instead of `.env` files in production:

```python
from azure.identity import DefaultAzureCredential
from azure.keyvault.secrets import SecretClient

credential = DefaultAzureCredential()
client = SecretClient(vault_url="https://your-vault.vault.azure.net/", credential=credential)

# Retrieve secrets
api_key = client.get_secret("ApiKey").value
```

### Use Managed Identities

For Azure-to-Azure communication:

```python
from azure.identity import DefaultAzureCredential

# No secrets needed!
credential = DefaultAzureCredential()
```

### Environment-Specific Configurations

Use separate `.env` files for each environment (all gitignored):

- `.env.development` - Dev environment
- `.env.staging` - Staging environment
- `.env.production` - Production environment

Load based on environment:

```python
env_file = f".env.{os.getenv('ENVIRONMENT', 'development')}"
load_dotenv(env_file)
```

---

## 📋 Pre-Push Checklist

Before pushing to GitHub:

- [ ] Verified `.env` is in `.gitignore`
- [ ] Ran `git status` - no `.env` listed
- [ ] Checked `git diff` - no secrets visible
- [ ] Reviewed `knowledge_sources.json` - only placeholders
- [ ] No hardcoded secrets in Python files
- [ ] `.env.example` is up to date

---

## 🔗 Additional Resources

- [OWASP Secret Management Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Secrets_Management_Cheat_Sheet.html)
- [Azure Key Vault Best Practices](https://learn.microsoft.com/azure/key-vault/general/best-practices)
- [GitHub Secret Scanning](https://docs.github.com/en/code-security/secret-scanning/about-secret-scanning)

---

## ⚖️ Compliance

This project handles:
- **Azure credentials** - Subject to Azure security policies
- **SharePoint data** - May contain PII/confidential information
- **API keys** - Unauthorized use could incur costs

Always follow your organization's:
- Data classification policies
- Secret management standards
- Incident response procedures

---

**Last Updated:** January 13, 2026

**Security Contact:** [Your Security Team Contact]
