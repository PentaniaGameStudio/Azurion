// Simple route toggler (Single Responsibility: view switching)
import { $, $$ } from '../core/dom.js';

export function initRouter(){
  const builderView = $('#builderView');
  const analyzerView = $('#analyzerView');
  const btnBuilder = $('#btnBuilder');
  const btnAnalyzer = $('#btnAnalyzer');

  btnBuilder.addEventListener('click', ()=> show('builder'));
  btnAnalyzer.addEventListener('click', ()=> show('analyzer'));

  function show(which){
    const isAnalyzer = which==='analyzer';
    analyzerView.classList.toggle('hidden', !isAnalyzer);
    builderView.classList.toggle('hidden', isAnalyzer);
    btnAnalyzer.classList.toggle('on', isAnalyzer);
    btnBuilder.classList.toggle('on', !isAnalyzer);
  }

  // default
  show('builder');
}