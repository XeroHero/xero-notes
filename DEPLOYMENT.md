# Vercel Deployment Guide

## Project Structure
This is a full-stack application with:
- Frontend: React app (Create React App) in `app/frontend/`
- Backend: FastAPI Python server in `app/backend/`

## Deployment Strategy

### Option 1: Frontend on Vercel + Backend on Separate Service (Recommended)

#### Frontend Deployment to Vercel
1. **Install Vercel CLI**:
   ```bash
   npm i -g vercel
   ```

2. **Configure Environment Variables**:
   - Update `app/frontend/.env.production` with your actual backend URL
   - Set up Firebase configuration in Vercel dashboard

3. **Deploy**:
   ```bash
   vercel --prod
   ```

#### Backend Deployment Options
- **Railway**: Easy Python deployment
- **Render**: Free tier available
- **AWS Elastic Beanstalk**: Scalable option
- **DigitalOcean App Platform**: Simple deployment

### Option 2: Convert to Next.js (Most Vercel-Friendly)

To fully leverage Vercel's capabilities, consider migrating from Create React App to Next.js:

1. **Benefits**:
   - Server-side rendering
   - API routes for backend functionality
   - Optimized builds
   - Better performance

2. **Migration Steps**:
   - Create new Next.js project
   - Move React components
   - Convert FastAPI routes to Next.js API routes
   - Update database connections

### Option 3: Serverless Functions

Convert FastAPI backend to Vercel serverless functions:

1. **Create `api/` directory structure**
2. **Convert each FastAPI route to individual serverless function**
3. **Handle database connections with proper connection pooling**

## Environment Variables Setup

### Vercel Environment Variables
Set these in your Vercel dashboard:
- `REACT_APP_BACKEND_URL`: Your production backend URL
- Firebase configuration variables
- Any other required API keys

### Backend Environment Variables
Your backend service will need:
- `MONGO_URL`: MongoDB connection string
- `DB_NAME`: Database name
- Firebase admin credentials
- Any other backend-specific variables

## Deployment Checklist

### Before Deployment
- [ ] Update all API URLs to use production endpoints
- [ ] Test build process locally: `cd app/frontend && npm run build`
- [ ] Verify environment variables are correctly configured
- [ ] Set up CORS on backend to allow your Vercel domain

### After Deployment
- [ ] Test all API endpoints
- [ ] Verify authentication flow works
- [ ] Check Firebase integration
- [ ] Monitor error logs

## Troubleshooting

### Common Issues
1. **CORS Errors**: Ensure backend allows requests from your Vercel domain
2. **Environment Variables**: Double-check all variables are set in Vercel dashboard
3. **Build Failures**: Check that all dependencies are properly installed
4. **API Timeouts**: Vercel functions have execution time limits

### Debugging
- Use Vercel logs to identify issues
- Test backend endpoints independently
- Verify network connectivity between frontend and backend

## Recommended Production Setup

For a production-ready setup:
1. **Frontend**: Vercel (automatic deployments from main branch)
2. **Backend**: Railway or Render (with database)
3. **Database**: MongoDB Atlas or similar
4. **Authentication**: Firebase Auth
5. **Monitoring**: Vercel Analytics + backend monitoring

This setup gives you:
- Automatic deployments
- Scalable infrastructure
- Good performance
- Easy maintenance
