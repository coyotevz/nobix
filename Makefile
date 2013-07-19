.PHONY: upload-docs

upload-docs:
	$(MAKE) -C docs html latex
	$(MAKE) -C docs/build/latex all-pdf
	cd docs/build/; mv html nobix-docs; zip -r nobix-docs.zip nobix-docs; mv nobix-docs html
	scp -r docs/build/html/* rocctech:webapps/rocctech_wsgi/htdocs/nobix/docs/
	scp -r docs/build/latex/Nobix.pdf rocctech:webapps/rocctech_wsgi/htdocs/nobix/docs/nobix-docs.pdf
	scp -r docs/build/nobix-docs.zip rocctech:webapps/rocctech_wsgi/htdocs/nobix/docs/
