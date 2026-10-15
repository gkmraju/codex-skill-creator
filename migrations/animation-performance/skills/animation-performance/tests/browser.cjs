/* Functional fixture checks; timing metrics are not an FPS/device benchmark. */
const {chromium}=require("playwright");
const fs=require("fs");
const path=require("path");
const {pathToFileURL}=require("url");
const assert=require("node:assert/strict");
const examples=path.resolve(__dirname,"../examples");
async function scenario(browser,name,reduced=false){
  const page=await browser.newPage({viewport:{width:960,height:720},reducedMotion:reduced?"reduce":"no-preference"});
  const errors=[];page.on("pageerror",error=>errors.push(error.message));
  await page.goto(pathToFileURL(path.join(examples,name+".html")).href);
  await page.waitForTimeout(80);
  const session=await page.context().newCDPSession(page);
  await session.send("Performance.enable");
  const initial=await page.locator("#card").boundingBox();
  const baseline=(await session.send("Performance.getMetrics")).metrics;
  await page.locator("#move").click();
  await page.waitForTimeout(350);
  const measured=(await session.send("Performance.getMetrics")).metrics;
  const moved=await page.locator("#card").boundingBox();
  const delta=field=>(measured.find(x=>x.name===field)?.value??0)-(baseline.find(x=>x.name===field)?.value??0);
  assert.ok(Math.abs(moved.x-initial.x-240)<1,"Final displacement must remain 240px");
  for(const key of ["width","height","y"])assert.ok(Math.abs(moved[key]-initial[key])<1,"Geometry changed: "+key);
  assert.equal(await page.locator("#move").getAttribute("aria-pressed"),"true");
  await page.locator("#action").click();assert.equal(await page.locator("#count").textContent(),"1");
  await page.locator("#action").focus();await page.keyboard.press("Enter");
  assert.equal(await page.locator("#count").textContent(),"2");
  assert.equal(await page.evaluate(()=>document.activeElement.id),"action");
  const styles=await page.locator("#card").evaluate(el=>({transitionProperty:getComputedStyle(el).transitionProperty,transitionDuration:getComputedStyle(el).transitionDuration,transform:getComputedStyle(el).transform}));
  if(reduced){
    const durations=styles.transitionDuration.split(",").map(x=>parseFloat(x));
    assert.ok(durations.every(x=>x===0),"Reduced motion must remove the unnecessary transition");
  }
  await page.locator("#move").focus();await page.keyboard.press("Space");
  await page.waitForTimeout(350);
  const returned=await page.locator("#card").boundingBox();
  assert.ok(Math.abs(returned.x-initial.x)<1,"Keyboard toggle must return to original position");
  assert.equal(await page.locator("#move").getAttribute("aria-pressed"),"false");
  assert.deepEqual(errors,[]);
  const result={fixture:name,reducedMotion:reduced,finalDisplacement:moved.x-initial.x,geometryPreserved:true,pointerAndKeyboardPassed:true,focusPreserved:true,styles,observedLayoutCount:delta("LayoutCount"),observedLayoutDurationSeconds:delta("LayoutDuration"),pageErrors:errors};
  await page.close();return result;
}
(async()=>{
 const options={headless:true};if(process.env.BROWSER_CHANNEL)options.channel=process.env.BROWSER_CHANNEL;
 const browser=await chromium.launch(options);
 try{
  const cases=[await scenario(browser,"before"),await scenario(browser,"after"),await scenario(browser,"after",true)];
  assert.ok(cases[1].observedLayoutCount<=cases[0].observedLayoutCount,"Corrected fixture should not add layout events in this controlled reproduction");
  const result={browserVersion:browser.version(),environment:"headless Chromium-family browser; desktop fixture only",cases,limits:"No FPS, GPU acceleration, real-phone or application-wide performance claim."};
  console.log(JSON.stringify(result,null,2));
 }finally{await browser.close()}
})().catch(error=>{console.error(error.stack||error.message);process.exitCode=1});
