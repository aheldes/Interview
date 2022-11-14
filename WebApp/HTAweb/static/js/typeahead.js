const params = 'action=query&list=search&format=json&origin=*'

new Autocomplete('#autocomplete', {
  
  // Search function can return a promise
  // which resolves with an array of
  // results. In this case we're using
  // the Wikipedia search API.
  search: input => {
    const url = `${substanceURL}/w/api.php?${
      params
    }&srsearch=${encodeURI(input)}`

    return new Promise(resolve => {
      if (input.length < 3) {
        return resolve([])
      }

      fetch(url)
        .then(response => response.json())
        .then(data => {
          const results = data.query.search.map((result, index) => {
            return { ...result, index }
          })
          resolve(results)
        })
    })
  },
  
  // Control the rendering of result items.
  // Let's show the title and snippet
  // from the Wikipedia results
  renderResult: (result, props) => {
    let group = ''
    if (result.index % 3 === 0) {
      group = `<li class="group">Group</li>`
    }
    return `
      ${group}
      <li ${props}>
        <div class="wiki-title">
          ${result.title}
        </div>
        <div class="wiki-snippet">
          ${result.snippet}
        </div>
      </li>
    `
  },
  
  // Wikipedia returns a format like this:
  //
  // {
  //   pageid: 12345,
  //   title: 'Article title',
  //   ...
  // }
  // 
  // We want to display the title
  getResultValue: result => result.title,

  // Open the selected article in
  // a new window
  onSubmit: result => {
    window.open(`${wikiUrl}/wiki/${
      encodeURI(result.title)
    }`)
  }
})