import '@testing-library/jest-dom/vitest';

// Polyfills for Recharts/Responsive behavior in JSDOM
class ResizeObserver {
  callback: ResizeObserverCallback;
  constructor(callback: ResizeObserverCallback) {
    this.callback = callback;
  }
  observe() {}
  unobserve() {}
  disconnect() {}
}
(globalThis as any).ResizeObserver = (globalThis as any).ResizeObserver || ResizeObserver;

// Some SVG measurements used by chart libs
if (!(SVGElement as any).prototype.getBBox) {
  (SVGElement as any).prototype.getBBox = () => ({
    x: 0,
    y: 0,
    width: 100,
    height: 100,
    top: 0,
    left: 0,
    right: 100,
    bottom: 100,
  });
}
