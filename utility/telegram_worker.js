addEventListener('fetch', event => {
  event.respondWith(handleRequest(event.request));
});

async function handleRequest(request) {
  const url = new URL(request.url);
  url.hostname = 'api.telegram.org';
  url.pathname = url.pathname.replace('/relay', '');
  return fetch(new Request(url, request));
}
