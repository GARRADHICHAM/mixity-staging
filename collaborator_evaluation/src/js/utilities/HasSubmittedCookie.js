const HasSubmittedCookie = {
	createCookie: function (name, value, days) {
		var date = new Date(),
			expires = '';
		if (days) {
			date.setTime(date.getTime() + days * 24 * 60 * 60 * 1000);
			expires = '; expires=' + date.toGMTString();
		} else {
			expires = '';
		}
		document.cookie = name + '=' + value + expires + '; path=/';
	},

	createHasSubmittedCookie: function () {
		this.createCookie('lgbt_sheet_submitted', 'true', 60);
	},

	checkHasSubmittedCookie: function () {
		var dc = document.cookie;
		var prefix = 'lgbt_sheet_submitted=';
		var begin = dc.indexOf('; ' + prefix);
		if (begin == -1) {
			begin = dc.indexOf(prefix);
			if (begin != 0) return null;
		} else {
			begin += 2;
			var end = document.cookie.indexOf(';', begin);
			if (end == -1) {
				end = dc.length;
			}
		}
		return decodeURI(dc.substring(begin + prefix.length, end));
	},
};

export default HasSubmittedCookie;
