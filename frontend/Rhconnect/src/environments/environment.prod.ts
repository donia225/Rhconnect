import packageInfo from '../../package.json';

export const environment = {
  production: true,
  apiUrl: 'http://127.0.0.1:8000/api',  // backend local avant le déploiement
  appVersion: packageInfo.version
};
