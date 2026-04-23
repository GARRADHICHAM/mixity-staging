import React, { useState, useEffect } from 'react';
import FiltersModal from './FiltersModal';

function ElearningsFilters({ elearnings, filters, setFilters }) {
	const [showFiltersModal, setShowFiltersModal] = useState(false);

	const updateFilter = (filterName, value) => {
		setFilters((prevFilters) => ({
			...prevFilters,
			[filterName]: value,
		}));
	};

	const handleTitleChange = (e) => {
		updateFilter('titleFilter', e.target.value);
	};

	const handleClose = () => setShowFiltersModal(false);

	const clearFilters = () => {
		setFilters({
			titleFilter: '',
			notionsFilter: [],
			keywordsFilter: [],
			categoriesFilter: [],
			evaluationMethodsFilter: [],
			languagesFilter: [],
		});
	};

	return (
		<div className="p-5 text-center">
			<h4 className="p-2">{gettext('Trouver un e-learning')}</h4>

			<div className="form-group" style={{ position: 'relative' }}>
				<input
					type="text"
					className="ps-5 m-1 border"
					style={{ backgroundColor: '#fff', borderRadius: '6px', width: '50%' }}
					value={filters.titleFilter}
					placeholder="Chercher un e-learning..."
					onChange={handleTitleChange}
				/>
				<button
					className="button border p-2 ms-2 align-middle"
					style={{ borderRadius: '6px', backgroundColor: '#fff', color: '#9094AA' }}
					onClick={() => setShowFiltersModal(true)}
				>
					<i className="bi bi-sliders2 pe-4"></i>
					{gettext('Filtres')}
				</button>
				<button
					className="button border p-2 ms-2 align-middle"
					style={{ borderRadius: '6px', backgroundColor: '#fff', color: '#9094AA' }}
					onClick={() => clearFilters()}
				>
					<i className="bi bi-trash2 pe-4"></i>
					{gettext('Vider les filtres')}
				</button>
			</div>

			<FiltersModal display={showFiltersModal} filters={filters} setFilters={setFilters} handleClose={handleClose} elearnings={elearnings} />
		</div>
	);
}

export default ElearningsFilters;
