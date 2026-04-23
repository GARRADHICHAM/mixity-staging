import React, { useState } from 'react';

const SavePopup = ({ message, onClose }) => {
	return (
		<div style={styles.popup}>
			<p>{message}</p>
			<button onClick={onClose} style={styles.closeButton}>
				X
			</button>
		</div>
	);
};

const styles = {
	popup: {
		position: 'fixed',
		bottom: '20px',
		right: '20px',
		padding: '10px',
		backgroundColor: '#4caf50',
		color: 'white',
		borderRadius: '5px',
		boxShadow: '0 0 10px rgba(0, 0, 0, 0.1)',
		display: 'flex',
		justifyContent: 'space-between',
		alignItems: 'center',
		minWidth: '200px',
	},
	closeButton: {
		display: 'none',
	},
};

export default SavePopup;
