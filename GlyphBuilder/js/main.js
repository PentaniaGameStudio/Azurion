// Composition root (Dependency Injection)
import { initRouter } from './app/router.js';
import { mountBuilder } from './ui/builderView.js';
import { mountAnalyzer } from './ui/analyzerView.js';

initRouter();
mountBuilder();
mountAnalyzer();