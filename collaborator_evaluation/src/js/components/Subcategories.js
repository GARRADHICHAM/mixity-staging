import React from 'react';
import './Subcategories.css';
import getSubcategories from '../utilities/getSubcategories';

export default function Subcategories(props) {
	const subcategoryList = getSubcategories(props.questions);
	function subcategoryClasses(subcategory, category) {
		if (props.currentSubcategory.slug === subcategory) {
			return categoryClasses(category);
		}
	}
	function categoryClasses(category) {
		if (
			(props.currentCategory !== undefined && props.currentCategory.name === category) ||
			(props.currentCategory === undefined && props.currentSubcategory.name === category)
		) {
			return 'bold space-top-and-bottom';
		}
	}

	function displaySubategory(category) {
		return categoryClasses(category) === undefined ? 'none' : '';
	}

	function styleColorFromSubcategoryList(category, subList) {
		if (displaySubategory(category) !== 'none') {
			if (subList.length > 0) {
				return { color: subList[0].color };
			}
			return { color: '#f67273' };
		}
	}

	function styleColorFromSubcategory(subcategory, category) {
		if (props.currentSubcategory.slug === subcategory.slug) {
			return { color: subcategory.color, display: displaySubategory(category) };
		}
		return { display: displaySubategory(category) };
	}

	return (
		<div style={{ marginBottom: '50px' }}>
			{Object.keys(subcategoryList).map((category) => (
				<div className="subcategories">
					<strong style={styleColorFromSubcategoryList(category, subcategoryList[category])} className={categoryClasses(category)}>
						{gettext(category)}
					</strong>
					{subcategoryList[category].map((subcategory) => (
						<li
							key={subcategory.slug}
							className={subcategoryClasses(subcategory.slug, category)}
							style={styleColorFromSubcategory(subcategory, category)}
						>
							&nbsp; &nbsp; &nbsp;- {gettext(subcategory.name)}
						</li>
					))}
				</div>
			))}{' '}
		</div>
	);
}
