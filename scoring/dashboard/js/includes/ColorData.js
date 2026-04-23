const colorData = {
	meanscore_sector: '#F2A71B',
	meanscore_sector_secondary: '#916410',
	meanscore_sector_list: ['#302105', '#916410', '#F2A71B', '#F7CA76', '#FCEDD1', '#F2A71B'],
	meanscore_global: '#863C63',
	meanscore_global_secondary: '#50243B',
	meanscore_global_list: ['#1A0C13', '#50243B', '#863C63', '#B68AA1', '#E6D8DF', '#863C63'],
	all: '#8888E2',
	all_secondary: '#515187',
	all_list: ['#272440', '#515187', '#8888E2', '#B7B7ED', '#E7E7F9', '#8888E2'],
	gender: '#FF6F6F',
	gender_secondary: '#994343',
	gender_list: ['#331616', '#994343', '#FF6F6F', '#FFA9A9', '#FFE2E2', '#FF6F6F'],
	disability: '#0099FF',
	disability_secondary: '#005B99',
	disability_list: ['#001E33', '#005B99', '#0099FF', '#66C1FF', '#CCEAFF', '#0099FF'],
	cultural_diversity: '#03A87C',
	cultural_diversity_secondary: '#006449',
	cultural_diversity_list: ['#002118', '#006449', '#03A87C', '#66CAAF', '#CCEDE4', '#03A87C'],
	generational_diversity: '#7A7697',
	generational_diversity_secondary: '#423C6B',
	generational_diversity_list: ['#272440', '#423C6B', '#7A7697', '#B3B1C3', '#ECEBF0', '#7A7697'],
	lgbt: '#47D4FF',
	lgbt_secondary: '#2A7F99',
	lgbt_list: ['#0E2A33', '#2A7F99', '#47D4FF', '#90E5FF', '#DAF6FF', '#47D4FF'],
	general_concept: '#FF6F6F',
	general_concept_secondary: '#401C1C',
	general_concept_list: ['#401C1C', '#994343', '#FF6F6F', '#FFA9A9', '#FFE2E2', '#FF6F6F'],
	professional_practice: '#0099FF',
	professional_practice_secondary: '#005B99',
	professional_practice_list: ['#001E33', '#005B99', '#0099FF', '#66C1FF', '#CCEAFF', '#0099FF'],
	cognitive_biases: '#03A87C',
	cognitive_biases_secondary: '#006449',
	cognitive_biases_list: ['#002118', '#006449', '#03A87C', '#66CAAF', '#CCEDE4', '#03A87C'],
	communication: '#423C6B',
	communication_secondary: '#7A7697',
	communication_list: ['#272440', '#423C6B', '#7A7697', '#B3B1C3', '#ECEBF0', '#7A7697'],
	professional_engagement: '#47D4FF',
	professional_engagement_secondary: '#2A7F99',
	professional_engagement_list: ['#0E2A33', '#2A7F99', '#47D4FF', '#90E5FF', '#DAF6FF', '#47D4FF'],
	csrd: '#000000',
	csrd_secondary: '#000000',
	csrd_list: ['#000000', '#000000', '#000000', '#000000', '#000000', '#000000'],
	white_labels: [
		'#302105', '#916410', '#1A0C13', '#50243B',
		'#863C63', '#272440', '#515187', '#331616',
		'#994343', '#001E33', '#005B99', '#002118',
		'#006449', '#272440', '#423C6B', '#7A7697',
		'#0E2A33', '#2A7F99', '#401C1C',
	],
	repartition_list: ['#18FBC0', '#21CBFF', '#22A6FF', '#6565A8', '#423C6B', '#22A6FF'],
};

function convertToRGB(hexa, alpha) {
	hexa = hexa.slice(1);
	if (hexa.length != 6) {
		return 'rgba(255, 255, 255, 0.1)';
	}

	var aRgbHex = hexa.match(/.{1,2}/g);
	var aRgb = `rgba(${parseInt(aRgbHex[0], 16)},${parseInt(aRgbHex[1], 16)},${parseInt(aRgbHex[2], 16)}, ${alpha})`;
	return aRgb;
}

export function getColors(colorKey, colors, alpha = null) {
	if (!colorKey.includes('_list'))
		if (alpha) return convertToRGB(colorData[colorKey], alpha);
		else return colorData[colorKey];
	else {
		if (alpha) {
			var returnColors = [];
			colors.map((color) => {
				returnColors.push(convertToRGB(colorData[colorKey][color - 1], alpha));
			});
		} else {
			var returnColors = [];
			colors.map((color) => {
				returnColors.push(colorData[colorKey][color - 1]);
			});
		}
		return returnColors;
	}
}

export function dataLabelColor(color) {
	if (colorData['white_labels'].includes(color)) return 'white';
	return '#181B3D';
}
