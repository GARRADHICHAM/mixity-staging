import React from 'react';
import './ProgressBar.css';

export default function ProgressBar(props) {
	const progressBarWidth = { width: `${props.progress}%` };
	return <div style={progressBarWidth} className="progress-bar"></div>;
}
