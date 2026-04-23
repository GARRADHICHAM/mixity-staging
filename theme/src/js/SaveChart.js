import domtoimage from './dom-to-image';
import JSZip from './jszip';
(function () {
	const out$ = (typeof exports !== 'undefined' && exports) || (typeof define !== 'undefined' && {}) || this || window;
	if (typeof define !== 'undefined') define('save-svg-as-png', [], () => out$);
	out$.default = out$;

	const xmlNs = 'http://www.w3.org/2000/xmlns/';
	const xhtmlNs = 'http://www.w3.org/1999/xhtml';
	const svgNs = 'http://www.w3.org/2000/svg';
	const doctype =
		'<?xml version="1.0" standalone="no"?><!DOCTYPE svg PUBLIC "-//W3C//DTD SVG 1.1//EN" "http://www.w3.org/Graphics/SVG/1.1/DTD/svg11.dtd" [<!ENTITY nbsp "&#160;">]>';
	const urlRegex = /url\(["']?(.+?)["']?\)/;
	const fontFormats = {
		woff2: 'font/woff2',
		woff: 'font/woff',
		otf: 'application/x-font-opentype',
		ttf: 'application/x-font-ttf',
		eot: 'application/vnd.ms-fontobject',
		sfnt: 'application/font-sfnt',
		svg: 'image/svg+xml',
	};

	const isElement = (obj) => obj instanceof HTMLElement || obj instanceof SVGElement;
	const requireDomNode = (el) => {
		if (!isElement(el)) throw new Error(`an HTMLElement or SVGElement is required; got ${el}`);
	};
	const requireDomNodePromise = (el) =>
		new Promise((resolve, reject) => {
			if (isElement(el)) resolve(el);
			else reject(new Error(`an HTMLElement or SVGElement is required; got ${el}`));
		});
	const isExternal = (url) => url && url.lastIndexOf('http', 0) === 0 && url.lastIndexOf(window.location.host) === -1;

	const getFontMimeTypeFromUrl = (fontUrl) => {
		const formats = Object.keys(fontFormats)
			.filter((extension) => fontUrl.indexOf(`.${extension}`) > 0)
			.map((extension) => fontFormats[extension]);
		if (formats) return formats[0];
		console.error(`Unknown font format for ${fontUrl}. Fonts may not be working correctly.`);
		return 'application/octet-stream';
	};

	const arrayBufferToBase64 = (buffer) => {
		let binary = '';
		const bytes = new Uint8Array(buffer);
		for (let i = 0; i < bytes.byteLength; i++) binary += String.fromCharCode(bytes[i]);
		return window.btoa(binary);
	};

	const getDimension = (el, clone, dim) => {
		const v =
			(el.viewBox && el.viewBox.baseVal && el.viewBox.baseVal[dim]) ||
			(clone.getAttribute(dim) !== null && !clone.getAttribute(dim).match(/%$/) && parseInt(clone.getAttribute(dim))) ||
			el.getBoundingClientRect()[dim] ||
			parseInt(clone.style[dim]) ||
			parseInt(window.getComputedStyle(el).getPropertyValue(dim));
		return typeof v === 'undefined' || v === null || isNaN(parseFloat(v)) ? 0 : v;
	};

	const getDimensions = (el, clone, width, height) => {
		if (el.tagName === 'svg') {
			return {
				width: width || getDimension(el, clone, 'width'),
				height: height || getDimension(el, clone, 'height'),
			};
		} else if (el.getBBox) {
			const { x, y, width, height } = el.getBBox();
			return {
				width: x + width,
				height: y + height,
			};
		}
	};

	const reEncode = (data) =>
		decodeURIComponent(
			encodeURIComponent(data).replace(/%([0-9A-F]{2})/g, (match, p1) => {
				const c = String.fromCharCode(`0x${p1}`);
				return c === '%' ? '%25' : c;
			}),
		);

	const uriToBlob = (uri) => {
		const byteString = window.atob(uri.split(',')[1]);
		const mimeString = uri.split(',')[0].split(':')[1].split(';')[0];
		const buffer = new ArrayBuffer(byteString.length);
		const intArray = new Uint8Array(buffer);
		for (let i = 0; i < byteString.length; i++) {
			intArray[i] = byteString.charCodeAt(i);
		}
		return new Blob([buffer], { type: mimeString });
	};

	const query = (el, selector) => {
		if (!selector) return;
		try {
			return el.querySelector(selector) || (el.parentNode && el.parentNode.querySelector(selector));
		} catch (err) {
			console.warn(`Invalid CSS selector "${selector}"`, err);
		}
	};

	const detectCssFont = (rule, href) => {
		// Match CSS font-face rules to external links.
		// @font-face {
		//   src: local('Abel'), url(https://fonts.gstatic.com/s/abel/v6/UzN-iejR1VoXU2Oc-7LsbvesZW2xOQ-xsNqO47m55DA.woff2);
		// }
		const match = rule.cssText.match(urlRegex);
		const url = (match && match[1]) || '';
		if (!url || url.match(/^data:/) || url === 'about:blank') return;
		const fullUrl = url.startsWith('../') ? `${href}/../${url}` : url.startsWith('./') ? `${href}/.${url}` : url;
		return {
			text: rule.cssText,
			format: getFontMimeTypeFromUrl(fullUrl),
			url: fullUrl,
		};
	};

	const inlineImages = (el) =>
		Promise.all(
			Array.from(el.querySelectorAll('image')).map((image) => {
				let href = image.getAttributeNS('http://www.w3.org/1999/xlink', 'href') || image.getAttribute('href');
				if (!href) return Promise.resolve(null);
				if (isExternal(href)) {
					href += (href.indexOf('?') === -1 ? '?' : '&') + 't=' + new Date().valueOf();
				}
				return new Promise((resolve, reject) => {
					const canvas = document.createElement('canvas');
					const img = new Image();
					img.crossOrigin = 'anonymous';
					img.src = href;
					img.onerror = () => reject(new Error(`Could not load ${href}`));
					img.onload = () => {
						canvas.width = img.width;
						canvas.height = img.height;
						canvas.getContext('2d').drawImage(img, 0, 0);
						image.setAttributeNS('http://www.w3.org/1999/xlink', 'href', canvas.toDataURL('image/png'));
						resolve(true);
					};
				});
			}),
		);

	const cachedFonts = {};
	const inlineFonts = (fonts) =>
		Promise.all(
			fonts.map(
				(font) =>
					new Promise((resolve, reject) => {
						if (cachedFonts[font.url]) return resolve(cachedFonts[font.url]);

						const req = new XMLHttpRequest();
						req.addEventListener('load', () => {
							// TODO: it may also be worth it to wait until fonts are fully loaded before
							// attempting to rasterize them. (e.g. use https://developer.mozilla.org/en-US/docs/Web/API/FontFaceSet)
							const fontInBase64 = arrayBufferToBase64(req.response);
							const fontUri = font.text.replace(urlRegex, `url("data:${font.format};base64,${fontInBase64}")`) + '\n';
							cachedFonts[font.url] = fontUri;
							resolve(fontUri);
						});
						req.addEventListener('error', (e) => {
							console.warn(`Failed to load font from: ${font.url}`, e);
							cachedFonts[font.url] = null;
							resolve(null);
						});
						req.addEventListener('abort', (e) => {
							console.warn(`Aborted loading font from: ${font.url}`, e);
							resolve(null);
						});
						req.open('GET', font.url);
						req.responseType = 'arraybuffer';
						req.send();
					}),
			),
		).then((fontCss) => fontCss.filter((x) => x).join(''));

	let cachedRules = null;
	const styleSheetRules = () => {
		if (cachedRules) return cachedRules;
		return (cachedRules = Array.from(document.styleSheets).map((sheet) => {
			try {
				return { rules: sheet.cssRules, href: sheet.href };
			} catch (e) {
				console.warn(`Stylesheet could not be loaded: ${sheet.href}`, e);
				return {};
			}
		}));
	};

	const inlineCss = (el, options) => {
		const { selectorRemap, modifyStyle, modifyCss, fonts } = options || {};
		const generateCss =
			modifyCss ||
			((selector, properties) => {
				const sel = selectorRemap ? selectorRemap(selector) : selector;
				const props = modifyStyle ? modifyStyle(properties) : properties;
				return `${sel}{${props}}\n`;
			});
		const css = [];
		const detectFonts = typeof fonts === 'undefined';
		const fontList = fonts || [];
		styleSheetRules().forEach(({ rules, href }) => {
			if (!rules) return;
			Array.from(rules).forEach((rule) => {
				if (typeof rule.style !== 'undefined') {
					if (query(el, rule.selectorText)) css.push(generateCss(rule.selectorText, rule.style.cssText));
					else if (detectFonts && rule.cssText.match(/^@font-face/)) {
						const font = detectCssFont(rule, href);
						if (font) fontList.push(font);
					} else css.push(rule.cssText);
				}
			});
		});

		return inlineFonts(fontList).then((fontCss) => css.join('\n') + fontCss);
	};

	out$.prepareSvg = (el, options, done) => {
		requireDomNode(el);
		const { left = 0, top = 0, width: w, height: h, scale = 1, responsive = false } = options || {};

		return inlineImages(el).then(() => {
			let clone = el.cloneNode(true);
			clone.style.backgroundColor = (options || {}).backgroundColor || el.style.backgroundColor;
			const { width, height } = getDimensions(el, clone, w, h);

			if (el.tagName !== 'svg') {
				if (el.getBBox) {
					if (clone.getAttribute('transform') != null) {
						clone.setAttribute('transform', clone.getAttribute('transform').replace(/translate\(.*?\)/, ''));
					}
					const svg = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
					svg.appendChild(clone);
					clone = svg;
				} else {
					console.error('Attempted to render non-SVG element', el);
					return;
				}
			}

			clone.setAttribute('version', '1.1');
			clone.setAttribute('viewBox', [left, top, width, height].join(' '));
			if (!clone.getAttribute('xmlns')) clone.setAttributeNS(xmlNs, 'xmlns', svgNs);
			if (!clone.getAttribute('xmlns:xlink')) clone.setAttributeNS(xmlNs, 'xmlns:xlink', 'http://www.w3.org/1999/xlink');

			if (responsive) {
				clone.removeAttribute('width');
				clone.removeAttribute('height');
				clone.setAttribute('preserveAspectRatio', 'xMinYMin meet');
			} else {
				clone.setAttribute('width', width * scale);
				clone.setAttribute('height', height * scale);
			}

			Array.from(clone.querySelectorAll('foreignObject > *')).forEach((foreignObject) => {
				foreignObject.setAttributeNS(xmlNs, 'xmlns', foreignObject.tagName === 'svg' ? svgNs : xhtmlNs);
			});

			return inlineCss(el, options).then((css) => {
				const style = document.createElement('style');
				style.setAttribute('type', 'text/css');
				style.innerHTML = `<![CDATA[\n${css}\n]]>`;

				const defs = document.createElement('defs');
				defs.appendChild(style);
				clone.insertBefore(defs, clone.firstChild);

				const outer = document.createElement('div');
				outer.appendChild(clone);
				const src = outer.innerHTML.replace(/NS\d+:href/gi, 'xmlns:xlink="http://www.w3.org/1999/xlink" xlink:href');

				if (typeof done === 'function') done(src, width, height);
				else return { src, width, height };
			});
		});
	};

	out$.svgAsDataUri = (el, options, done) => {
		requireDomNode(el);
		return out$.prepareSvg(el, options).then(({ src, width, height }) => {
			const svgXml = `data:image/svg+xml;base64,${window.btoa(reEncode(doctype + src))}`;
			if (typeof done === 'function') {
				done(svgXml, width, height);
			}
			return svgXml;
		});
	};

	out$.svgAsPngUri = (el, options, done) => {
		requireDomNode(el);
		const { encoderType = 'image/png', encoderOptions = 0.8, canvg } = options || {};

		const convertToPng = ({ src, width, height }) => {
			const canvas = document.createElement('canvas');
			const context = canvas.getContext('2d');
			const pixelRatio = window.devicePixelRatio || 1;

			canvas.width = width * pixelRatio;
			canvas.height = height * pixelRatio;
			canvas.style.width = `${canvas.width}px`;
			canvas.style.height = `${canvas.height}px`;
			context.setTransform(pixelRatio, 0, 0, pixelRatio, 0, 0);

			if (canvg) canvg(canvas, src);
			else context.drawImage(src, 0, 0);

			let png;
			try {
				png = canvas.toDataURL(encoderType, encoderOptions);
			} catch (e) {
				if ((typeof SecurityError !== 'undefined' && e instanceof SecurityError) || e.name === 'SecurityError') {
					console.error('Rendered SVG images cannot be downloaded in this browser.');
					return;
				} else throw e;
			}
			if (typeof done === 'function') done(png, canvas.width, canvas.height);
			return Promise.resolve(png);
		};
		if (canvg) {
			return out$.prepareSvg(el, options).then(convertToPng);
		} else {
			return out$.svgAsDataUri(el, options).then((uri) => {
				return new Promise((resolve, reject) => {
					const image = new Image();
					image.onload = () =>
						resolve(
							convertToPng({
								src: image,
								width: image.width,
								height: image.height,
							}),
						);
					image.onerror = () => {
						reject(
							`There was an error loading the data URI as an image on the following SVG\n${window.atob(uri.slice(26))}Open the following link to see browser's diagnosis\n${uri}`,
						);
					};

					image.src = uri;
				});
			});
		}
	};

	out$.download = (name, uri, options) => {
		if (navigator.msSaveOrOpenBlob) navigator.msSaveOrOpenBlob(uriToBlob(uri), name);
		else {
			const saveLink = document.createElement('a');
			if ('download' in saveLink) {
				saveLink.download = name;
				saveLink.style.display = 'none';
				document.body.appendChild(saveLink);
				try {
					const blob = uriToBlob(uri);
					const url = URL.createObjectURL(blob);
					saveLink.href = url;
					saveLink.onclick = () => requestAnimationFrame(() => URL.revokeObjectURL(url));
				} catch (e) {
					console.error(e);
					console.warn('Error while getting object URL. Falling back to string URL.');
					saveLink.href = uri;
				}
				saveLink.click();
				document.body.removeChild(saveLink);
			} else if (options && options.popup) {
				options.popup.document.title = name;
				options.popup.location.replace(uri);
			}
		}
	};

	out$.saveToBackend = (eval_id, name, uri, upload_url, csrftoken) => {
		var formData = new FormData();
		formData.append('footprint', uri);
		formData.append('csrfmiddlewaretoken', csrftoken);
		var request = new XMLHttpRequest();
		// param false => synchrone => wait for awnser
		request.open('POST', upload_url, true);
		request.setRequestHeader('X-CSRFToken', csrftoken);
		request.send(formData);
	};

	out$.saveSvgAsPng = (eval_id, name, options, upload_url, csrftoken, custom_element = null, dom_to_image = false) => {
		let el;
		if (custom_element == null) {
			el = document.getElementById('svg_radar_nolegend_' + eval_id);
		} else {
			el = custom_element;
		}
		if (dom_to_image) {
			let scale = 3;
			return domtoimage
				.toPng(el, {
					width: el.clientWidth * scale,
					height: el.clientHeight * scale,
					style: { transform: 'scale(' + scale + ')', 'transform-origin': 'top left' },
				})
				.then(function (dataUrl) {
					out$.saveToBackend(eval_id, name, dataUrl, upload_url, csrftoken);
				})
				.catch(function (error) {
					console.error('oops, something went wrong!', error);
				});
		} else {
			return requireDomNodePromise(el)
				.then((el) => out$.svgAsPngUri(el, options || {}))
				.then((uri) => out$.saveToBackend(eval_id, name, uri, upload_url, csrftoken));
		}
	};

	function htmlToDataURI(el, options, dom_to_image) {
		if (dom_to_image) {
			let scale = 3;
			return domtoimage.toPng(el, {
				width: el.clientWidth * scale,
				height: el.clientHeight * scale,
				style: { transform: 'scale(' + scale + ')', 'transform-origin': 'top left' },
			});
		} else {
			return requireDomNodePromise(el).then((el) => out$.svgAsPngUri(el, options || {}));
		}
	}

	function loadFontToSVG(svg, font_urls) {
		let promises = [];
		font_urls.forEach((font_url) => {
			promises.push(
				fetch(font_url)
					.then((response) => response.text())
					.then((response) => {
						svg.innerHTML = '<defs><style type="text/css">' + response + '</style></defs>' + svg.innerHTML;
					}),
			);
		});
		return Promise.all(promises);
	}

	function downloadBlob(blob, name = 'file.txt') {
		// Convert your blob into a Blob URL (a special url that points to an object in the browser's memory)
		const blobUrl = URL.createObjectURL(blob);

		// Create a link element
		const link = document.createElement('a');

		// Set link's href to point to the Blob URL
		link.href = blobUrl;
		link.download = name;

		// Append link to the body
		document.body.appendChild(link);

		// Dispatch click event on the link
		// This is necessary as link.click() does not work on the latest firefox
		link.dispatchEvent(
			new MouseEvent('click', {
				bubbles: true,
				cancelable: true,
				view: window,
			}),
		);

		// Remove link from body
		document.body.removeChild(link);
	}

	function convertFontStyleToProperty(targetElem) {
		var svgElem = targetElem.getElementsByTagName('text');
		for (const node of svgElem) {
			node.setAttribute('font-family', window.getComputedStyle(node, null).getPropertyValue('font-family'));
			node.replaceWith(node);
		}
	}

	function appendError(container, message) {
		if (container !== undefined) {
			container.innerHTML += '<div class="alert alert-danger" role="alert">' + message + '</div> ';
		}
	}

	function isDataURL(s) {
		return !!s.match(isDataURL.regex);
	}
	isDataURL.regex = /^\s*data:([a-z]+\/[a-z]+(;[a-z\-]+\=[a-z\-]+)?)?(;base64)?,[a-z0-9\!\$\&\'\,\(\)\*\+\,\;\=\-\.\_\~\:\@\/\?\%\s]*\s*$/i;

	out$.convertImagesToDataURI = (svg) => {
		var imageElem = Array.prototype.slice.call(svg.getElementsByTagName('image')).concat(Array.prototype.slice.call(svg.getElementsByTagName('img')));
		let i = 0;
		let fakesImages = [];
		for (const image of imageElem) {
			let image_href;
			if (image.src !== undefined) {
				image_href = image.src;
			} else {
				image_href = image.href.baseVal;
			}
			if (!isDataURL(image_href)) {
				let fakeImage = document.createElement('img');
				fakeImage.src = image_href;
				fakeImage.id = 'fakeImage' + i.toString();
				fakeImage.style.width = '500px';
				document.body.appendChild(fakeImage);
				i++;
				fakesImages.push([fakeImage, image]);
			}
		}
		return new Promise((r) => setTimeout(r, 500)).then((value) => {
			fakesImages.forEach((element) => {
				domtoimage.toPng(element[0]).then(function (dataUrl) {
					if (element[1].src !== undefined) {
						element[1].src = dataUrl;
					} else {
						element[1].href.baseVal = dataUrl;
					}
					document.body.removeChild(element[0]);
				});
			});
		});
	};

	out$.updateElement = (elem, font_url) => {
		convertFontStyleToProperty(elem);
		var svgElem = elem.getElementsByTagName('svg');
		let promises = [];
		for (const node of svgElem) {
			promises.push(loadFontToSVG(node, font_url));
		}
		return Promise.all(promises).then((e) => out$.convertImagesToDataURI(elem));
	};

	out$.downloadAllGraphs = (btn) => {
		var zip = new JSZip();
		btn.disabled = 'disabled';
		btn.style.cursor = 'not-allowed';
		let prev_promise = Promise.resolve();
		document.querySelectorAll('.downloadable_graph').forEach((elem) => {
			if (elem.style.backgroundColor === '') {
				elem.style.backgroundColor = '#1fe0';
			}
			prev_promise = prev_promise
				.then((e) =>
					htmlToDataURI(elem, { backgroundColor: '#1fe0' }, true).then((uri) => {
						var idx = uri.indexOf('base64,') + 'base64,'.length;
						var content = uri.substring(idx);
						btn.innerText = 'Sauvegarde de ' + elem.id + '.png ...';
						zip.file(elem.id + '.png', content, { base64: true });
					}),
				)
				.catch((reason) => {
					appendError(document.querySelector('#errors_container'), 'Erreur pour le graphique ' + elem.id + '.');
				});
		});
		prev_promise.then((e) => {
			zip.generateAsync({ type: 'blob' }).then(function (content) {
				btn.innerText = 'Télécharger tous les graphiques';
				btn.style.cursor = '';
				downloadBlob(content, 'graphs.zip');
			});
		});
	};
	out$.createDownloadButton = (elem, destination_container) => {
		let button = document.createElement('button');
		button.href = '#!';
		button.innerText = '⇩ Télécharger';
		button.className = 'action_button';
		button.setAttribute('disabled', 'disabled');
		button.style =
			'display:none;text-decoration: none;padding: 10px;background: #7fc3ff;color: white;font-weight: 600;border-radius: 32px;margin-right: 15px;';
		button.addEventListener('click', function () {
			if (elem.style.backgroundColor === '') {
				elem.style.backgroundColor = '#1fe0';
			}
			button.innerText = 'Chargement en cours...';
			button.setAttribute('disabled', 'disabled');
			button.style.cursor = 'not-allowed';
			htmlToDataURI(elem, { backgroundColor: '#1fe0' }, true).then((uri) => {
				fetch(uri)
					.then((res) => res.blob())
					.then((blob) => {
						button.innerText = '⇩ Télécharger';
						button.removeAttribute('disabled');
						button.style.cursor = '';
						downloadBlob(blob, elem.id + '.png');
					});
			});
		});
		destination_container.appendChild(button);
	};

	out$.updateAllThumbnails = (destination_container, from, to, buttonsClick) => {
		let button = document.createElement('button');
		button.href = '#!';
		let label = '⇧ Mettre à jour toutes les miniatures';
		button.innerText = label;
		button.className = 'action_button';
		button.setAttribute('disabled', 'disabled');
		button.style =
			'display:none;text-decoration: none;padding: 10px;background: rgb(120, 215, 117) none repeat scroll 0% 0%;color: white;font-weight: 600;border-radius: 32px;margin-right: 15px;';
		let promise = Promise.resolve();
		for (let i = 0; i < from.length; i++) {
			promise.then(() =>
				htmlToDataURI(from[i], { backgroundColor: '#1fe0' }, true).then((uri) => {
					to[i].setAttribute('src', uri);
				}),
			);
		}
		button.addEventListener('click', function () {
			buttonsClick.forEach((button) => {
				button.querySelector('.update_button').click();
			});
		});
		destination_container.appendChild(button);
	};

	out$.createUpdateButton = (elem, destination_container, upload_url, csrf_token, file_name, evaluation_id, dom_to_image) => {
		let button = document.createElement('button');
		button.href = '#!';
		let label = '⇧ Mettre à jour';
		button.innerText = label;
		button.className = 'action_button update_button';
		button.setAttribute('disabled', 'disabled');
		button.style =
			'display:none;text-decoration: none;padding: 10px;background: rgb(120, 215, 117) none repeat scroll 0% 0%;color: white;font-weight: 600;border-radius: 32px;margin-right: 15px;';
		button.addEventListener('click', function () {
			if (elem.style.backgroundColor === '') {
				elem.style.backgroundColor = '#1fe0';
			}
			let prev_label = button.innerText;
			button.innerText = 'Chargement en cours...';
			button.setAttribute('disabled', 'disabled');
			button.style.cursor = 'not-allowed';
			out$.saveSvgAsPng(evaluation_id, file_name, { backgroundColor: '#1fe0' }, upload_url, csrf_token, elem, dom_to_image)
				.then((e) => {
					alert(elem.id + ' sauvegardé avec succès');
					button.innerText = prev_label;
					button.removeAttribute('disabled');
					button.style.cursor = '';
				})
				.catch((e) => {
					console.log(e);
					alert('Erreur lors de la sauvegarde de ' + elem.id);
					button.innerText = prev_label;
					button.removeAttribute('disabled');
					button.style.cursor = '';
				});
		});
		destination_container.appendChild(button);
	};
})();

export function getCookie(name) {
	if (document.cookie && document.cookie != '') {
		var cookies = document.cookie.split(';');
		for (var i = 0; i < cookies.length; i++) {
			var cookie = jQuery.trim(cookies[i]);
			if (cookie.substring(0, name.length + 1) == name + '=') {
				return decodeURIComponent(cookie.substring(name.length + 1));
				break;
			}
		}
	}
}
