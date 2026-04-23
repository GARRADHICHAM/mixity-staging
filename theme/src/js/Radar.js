/* global d3 */
import RadialChart from './RadialChart';
import RadialLgbtChart from './RadialLgbtChart';
import RadialGenreChart from './RadialGenreChart';
import './SaveChart'; // !important

/**
 * Returns width and height of element with given id
 *
 * @export
 * @param {string} id
 * @returns
 */
export function calculateOffset(id) {
	const width = document.getElementById(id).offsetWidth;
	let height = width;
	height = (width * 6) / 6;
	return {
		width,
		height,
	};
}

/**
 * Returns random data for generate radar chart
 *
 * @export
 * @returns
 */
export function getRandomData(mirror = false) {
	var values = [
		Math.random() * (100 - 90) + 80,
		Math.random() * (100 - 80) + 80,
		Math.random() * (80 - 60) + 60,
		Math.random() * (90 - 70) + 70,
		Math.random() * (90 - 70) + 70,
	];
	var values_mirror = [
		Math.random() * (100 - 90) + 80,
		Math.random() * (100 - 80) + 80,
		Math.random() * (30 - 10) + 10,
		Math.random() * (70 - 50) + 50,
		Math.random() * (70 - 50) + 50,
	];

	function shuffleArray(array) {
		for (var i = array.length - 1; i > 0; i--) {
			var j = Math.floor(Math.random() * (i + 1));
			var temp = array[i];
			array[i] = array[j];
			array[j] = temp;
		}
	}

	shuffleArray(values);
	shuffleArray(values_mirror);

	var result = [
		{
			society: 'COGIP',
			measures: [
				{
					key: 'gender',
					label: gettext('Genre'),
					value: values[0],
				},
				{
					key: 'disability',
					label: gettext('Handicap'),
					value: values[1],
				},
				{
					key: 'cultural_diversity',
					label: gettext('Origines'),
					value: values[2],
				},
				{
					key: 'generational_diversity',
					label: gettext('Générations'),
					value: values[3],
				},
				{
					key: 'lgbt',
					label: gettext('LGBTQIA+'),
					value: values[4],
				},
			],
		},
	];

	if (mirror) {
		result.push({
			society: 'LALA',
			measures: [
				{
					key: 'gender',
					label: gettext('Genre'),
					value: values_mirror[0],
				},
				{
					key: 'disability',
					label: gettext('Handicap'),
					value: values_mirror[1],
				},
				{
					key: 'cultural_diversity',
					label: gettext('Origines'),
					value: values_mirror[2],
				},
				{
					key: 'generational_diversity',
					label: gettext('Générations'),
					value: values_mirror[3],
				},
				{
					key: 'lgbt',
					label: gettext('LGBTQIA+'),
					value: values_mirror[4],
				},
			],
		});
	}

	return result;
}

/**
 * Initialize Radar graph on element with given id
 * If no data provided, it generates random graph
 *
 * @export
 * @param {string} id
 * @param {array} [data=getRandomData()]
 */
export function initRadar(id, data = getRandomData(), mirror, enableLegend, enableLinks) {
	data = data.replace(/'/g, '"');
	if (typeof data === 'string') {
		if (data === '') {
			data = getRandomData(Boolean(mirror));
		} else {
			data = JSON.parse(data);
		}
	}
	const { width, height } = calculateOffset(id);
	const svg = d3.select(`#${id}`).append('svg').attr('id', `svg_${id}`).attr('width', width).attr('height', height);
	const chart = new RadialChart(`svg_${id}`);
	chart.initData(data, { enableInteraction: true, mirrorsvg: mirror, enableLegend: enableLegend, enableLinks: enableLinks });
}

/**
 * Main loop
 */
$(document).ready(function () {
	document.fonts.ready.then(function () {
		// Rendering the three types of footprints
		const radarElementsWithLegend = document.querySelectorAll('[id^="radar_"]');
		for (let index = 0; index < radarElementsWithLegend.length; index++) {
			const element = radarElementsWithLegend[index];
			let no_legend_found = element.id.indexOf('nolegend');
			let no_links_found = element.id.indexOf('nolinks');
			console.log('Mirrrror is :', element.dataset.mirror);
			initRadar(element.id, element.dataset.radar, element.dataset.mirror, no_legend_found < 0, no_links_found < 0);
		}
	}); // IMPORTANT timeout to wait until fonts are loaded
});
