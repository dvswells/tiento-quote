# Deploying Tiento Quote to Render

This guide explains how to deploy the Tiento Quote CNC machining calculator to Render.

## Prerequisites

1. A [Render account](https://render.com) (free tier available)
2. Your code pushed to a Git repository (GitHub, GitLab, or Bitbucket)
3. The `config/pricing_coefficients.json` file committed to your repo

## Deployment Options

### Option 1: Using Blueprint (Recommended)

This method uses the `render.yaml` file for automated deployment.

1. **Push your code to GitHub/GitLab/Bitbucket**
   ```bash
   git push origin main  # or your main branch name
   ```

2. **Create a new Blueprint in Render**
   - Go to https://dashboard.render.com/blueprints
   - Click "New Blueprint Instance"
   - Connect your repository
   - Render will automatically detect `render.yaml`
   - Click "Apply" to deploy

3. **Wait for deployment**
   - Initial deployment takes 5-10 minutes (CadQuery is large)
   - Watch the logs for any errors

4. **Access your app**
   - Once deployed, Render provides a URL like `https://tiento-quote.onrender.com`

### Option 2: Manual Web Service Setup

If you prefer manual configuration:

1. **Create a New Web Service**
   - Go to https://dashboard.render.com/
   - Click "New +" → "Web Service"
   - Connect your repository

2. **Configure the service**
   - **Name**: `tiento-quote`
   - **Region**: Choose closest to your users (e.g., Frankfurt, Oregon)
   - **Branch**: `main` (or your branch name)
   - **Runtime**: Python 3
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `bash start.sh`
   - **Plan**: Free (or Starter for production)

3. **Add Environment Variables** (optional)
   - `PYTHON_VERSION`: `3.11`
   - `DATABASE_PATH`: `training/training_data.db`
   - `UPLOADS_PATH`: `uploads`
   - `TEMP_PATH`: `temp`

4. **Create a Disk** (for persistent storage)
   - In the service settings, go to "Disks"
   - Click "Add Disk"
   - **Name**: `tiento-data`
   - **Mount Path**: `/opt/render/project/src`
   - **Size**: 1 GB (free tier limit)

5. **Deploy**
   - Click "Create Web Service"
   - Wait for deployment (5-10 minutes)

## Important Notes

### Free Tier Limitations

- **Sleep after 15 minutes of inactivity**: First request after sleep takes 30-60 seconds
- **750 hours/month**: Shared across all free services
- **Limited resources**: 512MB RAM, 0.1 CPU

### Upgrading to Paid Plan

For production use, consider upgrading to **Starter ($7/month)** or higher:
- No sleep/spin-down
- More resources (512MB+ RAM)
- Better performance for CadQuery operations

### File Uploads

- Uploaded STEP files are stored in the `uploads/` directory
- With the disk configuration, files persist between deployments
- Without a disk, uploads are lost when the service restarts

### Pricing Model

- The app uses `config/pricing_coefficients.json` for pricing
- Ensure this file is committed to your repository
- To update the model, retrain using `training/train_model.py` and commit the new config

## Troubleshooting

### Deployment fails during pip install

**Problem**: CadQuery installation times out or fails

**Solution**:
- Render's free tier has limited resources
- Try upgrading to Starter plan for more build resources
- Or reduce the `requirements.txt` to essential packages only

### App shows "Application Error"

**Problem**: Streamlit fails to start

**Solution**:
1. Check the logs in Render dashboard
2. Ensure `start.sh` has execute permissions (it should by default)
3. Verify all environment variables are set correctly

### 3D Viewer doesn't show STL

**Problem**: STL conversion fails

**Solution**:
- Ensure `packages.txt` system dependencies are installed
- Check logs for CadQuery errors
- Verify the STEP file is valid

### Database errors

**Problem**: SQLite database issues

**Solution**:
- Ensure the `training/` directory exists
- Check disk is mounted correctly at `/opt/render/project/src`
- Verify `DATABASE_PATH` environment variable

### Port binding errors

**Problem**: App can't bind to port

**Solution**:
- Render automatically sets the `PORT` environment variable
- The `start.sh` script uses `${PORT:-8501}` to handle this
- Don't hardcode port 8501 in Streamlit config

## Monitoring

- **Logs**: View real-time logs in Render dashboard under "Logs" tab
- **Metrics**: Monitor CPU, memory, and bandwidth usage
- **Alerts**: Set up email notifications for deployment failures

## Updating the App

1. Push changes to your repository
   ```bash
   git add .
   git commit -m "Update app"
   git push origin main
   ```

2. Render automatically redeploys on push (if auto-deploy is enabled)
   - Or manually deploy from Render dashboard

## Custom Domain

To use your own domain (e.g., `quote.wellsglobal.eu`):

1. Go to service settings in Render
2. Click "Custom Domain"
3. Add your domain
4. Update DNS records as instructed by Render
5. Render provides free SSL certificates via Let's Encrypt

## Security Recommendations

For production deployment:

1. **Enable XSRF protection** in `start.sh`:
   - Remove `--server.enableXsrfProtection=false`

2. **Configure CORS properly**:
   - Update CORS settings based on your domain

3. **Add authentication** if needed:
   - Consider Streamlit's built-in auth or custom solution

4. **Validate uploads strictly**:
   - The app already validates STEP files
   - Consider adding virus scanning for production

5. **Rate limiting**:
   - Add rate limiting to prevent abuse
   - Render doesn't provide this built-in on free tier

## Cost Estimate

**Free Tier**: $0/month
- Good for testing and demo
- Sleeps after inactivity

**Production Setup**: ~$7-21/month
- Starter plan ($7/mo): No sleep, 512MB RAM
- Standard plan ($21/mo): 2GB RAM, better for heavy CAD processing

## Support

If you encounter issues:
1. Check Render's [documentation](https://render.com/docs)
2. Review the logs in Render dashboard
3. Check the [Render community forum](https://community.render.com/)
4. Contact Render support (paid plans get priority support)
