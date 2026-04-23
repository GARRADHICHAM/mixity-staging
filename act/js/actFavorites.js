import React from 'react';
import ReactDOM from 'react-dom';
import Favorites from './FavoritesList';

ReactDOM.render(
	<React.StrictMode>
		<Favorites />
	</React.StrictMode>,
	document.getElementById('favorites_list'),
);
