import { QuestionTypeGeneratorComponent } from './QuestionTypeGeneratorComponent';
import { createRoot } from 'react-dom/client';
import React from 'react';
const rootElement = document.getElementById('question-type-generator');
createRoot(rootElement).render(<QuestionTypeGeneratorComponent />);
