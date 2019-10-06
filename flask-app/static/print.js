// -*- mode: js; js-indent-level: 2; -*-

var app = new Vue({
  el: '#wordprint',
  data: {
    wordText: "今天不努力工作，明天努力找工作。",
    title: "汉字练习",
  },
  computed: {
  },
  watch: {
  },
  methods: {
    sendPrintWords: function(event) {
      var self = this;
      console.log('sending words:' + self.wordText);
      $.ajax({
	type: 'POST',
	url: "/print",
	dataType: 'json',
	data: { wordText: self.wordText, title: self.title },
	success: function(data) {
    	  console.log(data);
    	},
      });
      console.log("passed ?");
    },
  },
  mounted: function() {
    var self = this;
    // $.ajax({
    //   type: 'GET',
    //   url: "words",
    //   dataType: 'json',
    //   success: function(data) {
    // 	console.log(data);
    // 	self.words.splice(0);
    // 	self.totalWords = data.totalWords;
    // 	for (var i = 0; i < data.words.length; ++i) {
    // 	  data.words[i].score = 0;
    // 	  data.words[i].skip = false;
    // 	  // data.words[i].dateStudy = '';
    // 	  self.words.push(data.words[i]);
    // 	  if(self.activeWords.length < self.nmax) self.activeWords.push(self.words[i]);
    // 	}
    // 	self.today = data.today;
    // 	console.log("today: ", data.today);
    // 	console.log("daily: ", data.daily);
    // 	if (data.daily[data.today]) {
    // 	  self.passed = data.daily[data.today][0];
    // 	  self.failed = data.daily[data.today][1];
    // 	  self.points = data.daily[data.today][2];
    // 	}
    // 	self.totalPoints = data.totalPoints;
    // 	self.totalDays = data.totalDays;
    // 	self.totalStudyDays = data.totalStudyDays;
    // 	self.firstDay = data.firstDay;
    //     self.reviewDays.splice(0);
    //     self.reviewDays.push(...data.reviewDays);
    // 	self.bookList.splice(0);
    // 	console.log(data.bookList);
    // 	for(var i = 0; i < data.bookList.length; ++i) {
    // 	  self.bookList.splice(i, 1, data.bookList[i]);
    // 	}
    // 	console.log(self.bookList);
    //   }
    // });
    // console.log("passed ?");
  },
})
