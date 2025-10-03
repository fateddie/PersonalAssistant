# Production Deployment Guide

## 🚀 Deploy to Vercel (Recommended)

Your Personal Assistant app is optimized for Vercel deployment with automated CI/CD.

---

## Prerequisites

- [ ] GitHub account with repository
- [ ] Vercel account (free tier works)
- [ ] All environment variables ready
- [ ] Tests passing locally

---

## Step 1: Push to GitHub

### Create Repository
```bash
# If not already on GitHub
git remote add origin https://github.com/YOUR_USERNAME/personal-assistant.git
git branch -M main
git push -u origin main
```

### Current Branch Status
You're on: `feature/test-coaching`

**Recommended:** Merge to main first
```bash
git checkout main || git checkout -b main
git merge feature/test-coaching
git push origin main
```

---

## Step 2: Connect to Vercel

### Option A: Vercel Dashboard (Easiest)

1. Go to [vercel.com](https://vercel.com)
2. Click "Add New Project"
3. Import your GitHub repository
4. Select "personal-assistant" repo
5. Vercel auto-detects Next.js settings ✅

### Option B: Vercel CLI

```bash
npm i -g vercel
vercel login
vercel
# Follow prompts
```

---

## Step 3: Configure Environment Variables

### In Vercel Dashboard:
**Settings → Environment Variables → Add**

#### Required Variables:

```bash
# Supabase
NEXT_PUBLIC_SUPABASE_URL=https://coxnsvusaxfniqivhlar.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
SUPABASE_SERVICE_ROLE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...

# OpenAI
OPENAI_API_KEY=sk-proj-...

# Google OAuth
GOOGLE_CLIENT_ID=1069421989747-57o22m4h20tpnemegpv2tu01g9murkv8.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=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

# NextAuth
NEXTAUTH_URL=https://your-app.vercel.app
NEXTAUTH_SECRET=F0wnM5vp/Rp9uuC6wr/W445GLHbtTMb8zQueYFxlbs0=

# App
NEXT_PUBLIC_APP_URL=https://your-app.vercel.app
```

#### Important Notes:
- ✅ Set all variables for **Production** environment
- ✅ Update `NEXTAUTH_URL` to your Vercel domain
- ✅ Update `NEXT_PUBLIC_APP_URL` to your Vercel domain
- ✅ Keep API keys secure - never commit to git

---

## Step 4: Update Google OAuth

### After First Deployment:

1. **Get your Vercel URL** (e.g., `personal-assistant-xyz.vercel.app`)

2. **Update Google Cloud Console:**
   - Go to [console.cloud.google.com](https://console.cloud.google.com)
   - Navigate to: APIs & Services → Credentials
   - Edit your OAuth 2.0 Client
   - Add Authorized JavaScript origins:
     ```
     https://personal-assistant-xyz.vercel.app
     ```
   - Add Authorized redirect URIs:
     ```
     https://personal-assistant-xyz.vercel.app/api/auth/callback/google
     ```

3. **Update Supabase Redirect URLs:**
   - Go to Supabase Dashboard
   - Authentication → URL Configuration
   - Add Site URL: `https://personal-assistant-xyz.vercel.app`
   - Add Redirect URLs: `https://personal-assistant-xyz.vercel.app/**`

---

## Step 5: Enable GitHub Actions Auto-Deploy

### Your CI/CD Pipeline is Ready!

The pipeline (`.github/workflows/ci.yml`) will:
- ✅ Run on every push to main
- ✅ Check TypeScript & ESLint
- ✅ Run Playwright tests
- ✅ Verify build succeeds
- ✅ Scan for security issues

### Add Vercel Token (Optional)

For automatic deployment from GitHub Actions:

1. **Get Vercel Token:**
   - Vercel Dashboard → Settings → Tokens
   - Create new token
   - Copy token value

2. **Add to GitHub Secrets:**
   - GitHub repo → Settings → Secrets → Actions
   - Add new secret: `VERCEL_TOKEN`
   - Paste token value

3. **Uncomment deployment in ci.yml:**
   ```yaml
   # Line 113 in .github/workflows/ci.yml
   - name: Deploy to Vercel
     run: vercel --prod --token=${{ secrets.VERCEL_TOKEN }}
   ```

---

## Step 6: Verify Deployment

### Post-Deployment Checklist:

#### Basic Functionality
- [ ] App loads at Vercel URL
- [ ] Homepage renders correctly
- [ ] No console errors
- [ ] Mobile responsive

#### Authentication
- [ ] Google OAuth redirects work
- [ ] Login/logout successful
- [ ] Session persists
- [ ] User profile loads

#### Core Features
- [ ] Task Manager loads
- [ ] Habit Tracker loads
- [ ] Voice Control button appears
- [ ] Dashboard data displays

#### AI Voice Commands
- [ ] Microphone activation works
- [ ] Voice recognition active
- [ ] OpenAI processing succeeds
- [ ] Tasks/habits created via voice
- [ ] Text-to-speech responses

#### Performance
- [ ] Page load < 3 seconds
- [ ] Dashboard cached properly
- [ ] No white screen issues
- [ ] Mobile performance acceptable

---

## Monitoring & Maintenance

### Vercel Dashboard Monitoring

**Analytics:**
- Page views
- Response times
- Error rates
- Traffic patterns

**Logs:**
- Real-time function logs
- Error tracking
- API call monitoring

### OpenAI Usage Monitoring

1. **OpenAI Dashboard:**
   - [platform.openai.com/usage](https://platform.openai.com/usage)
   - Monitor daily API calls
   - Track costs
   - Set usage alerts

2. **Expected Usage:**
   - ~$0.0002 per voice command
   - 100 commands/day = $0.02/day
   - Monitor for anomalies

### Supabase Monitoring

1. **Database:**
   - Dashboard → Database → Statistics
   - Monitor query performance
   - Check storage usage

2. **Auth:**
   - Monitor login success rate
   - Track active users
   - Review OAuth flows

---

## Rollback Plan

### If Issues Arise:

1. **Quick Rollback:**
   - Vercel Dashboard → Deployments
   - Find last working deployment
   - Click "..." → Promote to Production

2. **Fix Forward:**
   ```bash
   git revert HEAD
   git push origin main
   # Vercel auto-deploys fixed version
   ```

3. **Disable Features:**
   ```bash
   # In Vercel env vars, temporarily remove:
   OPENAI_API_KEY
   # Voice commands will use fallback mode
   ```

---

## Scaling Considerations

### Performance Optimization

**Current Setup:**
- ✅ Dashboard caching (5 minutes)
- ✅ Static page generation
- ✅ API route caching
- ✅ Image optimization

**Next Level:**
- Add Redis for distributed caching
- Implement SWR for client-side caching
- Enable Vercel Edge Functions
- Add CDN for static assets

### Cost Optimization

**Vercel Free Tier Limits:**
- 100GB bandwidth/month
- 100 deployments/day
- 1000 serverless function hours/month

**OpenAI Optimization:**
- Use gpt-4o-mini (already done ✅)
- Implement request caching
- Add rate limiting per user
- Monitor and alert on high usage

### Security Enhancements

**Already Implemented:**
- ✅ Environment variable protection
- ✅ API authentication required
- ✅ CORS configured
- ✅ NextAuth CSRF protection

**Additional Measures:**
- Add rate limiting middleware
- Implement request logging
- Set up error monitoring (Sentry)
- Enable Vercel Web Application Firewall

---

## Troubleshooting

### Build Failures

**Issue:** Vercel build fails
**Solutions:**
1. Check build logs in Vercel dashboard
2. Verify all env vars are set
3. Test build locally: `npm run build`
4. Check Node.js version (should be 22)

### OAuth Issues

**Issue:** Google OAuth not working in production
**Solutions:**
1. Verify redirect URIs in Google Console
2. Check `NEXTAUTH_URL` matches Vercel domain
3. Ensure `GOOGLE_CLIENT_ID` and `SECRET` correct
4. Test in incognito mode

### API Errors

**Issue:** OpenAI API calls failing
**Solutions:**
1. Verify `OPENAI_API_KEY` in Vercel env vars
2. Check OpenAI API status
3. Review function logs in Vercel
4. Verify API quota not exceeded

### Database Connection

**Issue:** Supabase connection fails
**Solutions:**
1. Check Supabase project status
2. Verify URL and keys in Vercel
3. Test direct connection from Vercel logs
4. Check Supabase connection pooling

---

## Success Checklist

### Pre-Deployment
- [x] All tests passing locally
- [x] Environment variables documented
- [x] Git repository clean
- [x] Branch merged to main

### Deployment
- [ ] Vercel project created
- [ ] All env vars configured
- [ ] Google OAuth updated
- [ ] Supabase URLs updated
- [ ] First deployment successful

### Post-Deployment
- [ ] App accessible at URL
- [ ] All features working
- [ ] Voice commands functional
- [ ] Monitoring enabled
- [ ] Team notified

---

## Next Steps

1. **Deploy Now:** Push to GitHub and watch CI/CD magic happen
2. **Test Thoroughly:** Use voice commands in production
3. **Monitor Closely:** Watch logs for first 24 hours
4. **Gather Feedback:** Share with test users
5. **Iterate:** Make improvements based on usage

---

## Support Resources

- **Vercel Docs:** [vercel.com/docs](https://vercel.com/docs)
- **Next.js Docs:** [nextjs.org/docs](https://nextjs.org/docs)
- **OpenAI Docs:** [platform.openai.com/docs](https://platform.openai.com/docs)
- **Supabase Docs:** [supabase.com/docs](https://supabase.com/docs)

---

**Ready to Deploy?** 🚀

```bash
git push origin main
# Watch your CI/CD pipeline deploy automatically!
```
