export function copyToClipboard(text) {
	navigator.clipboard.writeText(text).then(
		function () {
			return;
		},
		function (err) {
			throw new Error('Could not copy text: ', err);
		},
	);
}
