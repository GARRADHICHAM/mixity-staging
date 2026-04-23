import React, { useState, useEffect } from 'react';

const CountriesList = ({ onCountryChange }) => {
	const [countries, setCountries] = useState([]);
	const [filteredCountries, setFilteredCountries] = useState([]);
	const [selectedCountry, setSelectedCountry] = useState('');
	const [searchTerm, setSearchTerm] = useState('');

	useEffect(() => {
		const fetchCountries = async () => {
			try {
				const response = await fetch('/api/countries/');
				if (!response.ok) {
					throw new Error('Network response was not ok');
				}
				const data = await response.json();
				setCountries(data);
				setFilteredCountries(data);
			} catch (error) {
				console.error('There was an error fetching the country list!', error);
			}
		};

		fetchCountries();
	}, []);

	useEffect(() => {
		// Filter countries based on the search term
		const filtered = countries.filter((country) => country.name.toLowerCase().includes(searchTerm.toLowerCase()));
		setFilteredCountries(filtered);
	}, [searchTerm, countries]);

	const handleSearchChange = (event) => {
		setSearchTerm(event.target.value);
	};

	const handleSelectChange = (event) => {
		const selectedCode = event.target.value;
		setSelectedCountry(selectedCode);
		if (onCountryChange) {
			onCountryChange(selectedCode);
		}
	};

	return (
		<select
			style={{ background: '#F6F7FB', borderColor: '#F6F7FB', margin: 0, borderRadius: '8px', whiteSpace: 'nowrap', boxShadow: 'none' }}
			value={selectedCountry}
			onChange={handleSelectChange}
			required
		>
			<option value="">
				<input type="text" value={searchTerm} onChange={handleSearchChange} placeholder={gettext('Rechercher un pays...')} />
			</option>
			{filteredCountries.map((country) => (
				<option key={country.code.toLowerCase()} value={country.code.toLowerCase()}>
					{country.name}
				</option>
			))}
		</select>
	);
};

export default CountriesList;
