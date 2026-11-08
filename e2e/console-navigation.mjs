// @spec docs/BACKLOG.md#sls-067 | docs/FUNCTION_CATALOGUE.md#parcours-et-adresses
// @verifies docs/BACKLOG.md#sls-067 | docs/FUNCTION_CATALOGUE.md#réalisation-et-preuves
// Existing scenarios enter through the real home and visible navigation.
export async function enterNamespaces(page,base){
  await page.goto(base);
  await page.getByRole('heading',{name:'Fonctions',exact:true}).waitFor();
  const link=page.getByRole('complementary',{name:'Navigation principale',exact:true}).getByRole('link',{name:'Namespaces',exact:true});
  if(!await link.isVisible())await page.getByRole('button',{name:'Menu',exact:true}).click();
  await link.click();
  await page.waitForURL(base+'/console/namespaces');
  await page.getByRole('heading',{name:'Namespaces',exact:true}).waitFor();
}
