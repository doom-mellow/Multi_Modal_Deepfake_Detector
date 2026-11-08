import { createRoot } from 'react-dom/client';

import App from './App';
import './index.css';

import { AppWrapper } from './components/common/PageMeta';

const rootElement = document.getElementById('root');

if (!rootElement) {
  throw new Error('Root element was not found.');
}

createRoot(rootElement).render(
  <AppWrapper>
    <App />
  </AppWrapper>
);