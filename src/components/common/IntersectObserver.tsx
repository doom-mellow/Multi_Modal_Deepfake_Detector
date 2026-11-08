import { useEffect } from 'react';
import { useLocation } from 'react-router-dom';
import { Observer } from 'tailwindcss-intersect';

const IntersectObserver = () => {
  const { pathname } = useLocation();

  useEffect(() => {
    // Restart the observer after the new page has rendered.
    const timer = window.setTimeout(() => {
      Observer.restart();
    }, 100);

    return () => {
      window.clearTimeout(timer);
    };
  }, [pathname]);

  return null;
};

export default IntersectObserver;