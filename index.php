<?php
// Постраничный просмотр статей: 1 группа (игра) = 1 страница. Бан группы пишется в banned.txt
// Данные статей — articles.tsv (id, title, link, date, author, image, excerpt),
// игры статьи — titles_result3.txt (строки «id N - Игра1, Игра2»).
$ART    = __DIR__.'/articles.tsv';
$GAMES  = __DIR__.'/titles_result3.txt';
$BANF   = __DIR__.'/banned.txt';

// --- загрузка банов ---
function load_banned($f){
  if(!is_file($f)) return [];
  $a=array_filter(array_map('trim', file($f, FILE_IGNORE_NEW_LINES)));
  return array_flip($a);
}

// --- обработка бана/разбана (POST) ---
if($_SERVER['REQUEST_METHOD']==='POST' && isset($_POST['game'])){
  $g = trim($_POST['game']);
  $act = isset($_POST['act']) ? $_POST['act'] : 'ban';
  $banned = load_banned($BANF);
  if($act==='ban'   && $g!=='' && !isset($banned[$g])) file_put_contents($BANF, $g."\n", FILE_APPEND|LOCK_EX);
  if($act==='unban' && $g!=='' &&  isset($banned[$g])){
    $keep = array();
    foreach(array_keys($banned) as $x){ if($x!==$g) $keep[]=$x; }
    file_put_contents($BANF, $keep ? implode("\n",$keep)."\n" : '', LOCK_EX);
  }
  $q = isset($_GET['sug']) ? '?sug=1' : (isset($_GET['i']) ? '?i='.(int)$_GET['i'] : '');
  header('Location: '.strtok($_SERVER['REQUEST_URI'],'?').$q);
  exit;
}

// --- загрузка статей из articles.tsv: id => данные ---
$banned = load_banned($BANF);
$arts = array();
if(($fh=fopen($ART,'r'))!==false){
  fgets($fh); // заголовок
  while(($line=fgets($fh))!==false){
    $line=rtrim($line,"\r\n");
    if($line==='') continue;
    $f=explode("\t",$line);
    $id=preg_replace('/^\xEF\xBB\xBF/','',$f[0]);
    $arts[$id]=array(
      'title'=>isset($f[1])?$f[1]:'', 'link'=>isset($f[2])?$f[2]:'', 'date'=>isset($f[3])?$f[3]:'',
      'author'=>isset($f[4])?$f[4]:'', 'img'=>isset($f[5])?$f[5]:'', 'excerpt'=>isset($f[6])?$f[6]:'',
    );
  }
  fclose($fh);
}

// --- группировка по играм из titles_result3.txt (порядок как в файле) ---
// Статьи с одной игрой группируются по игре. Статья с несколькими играми (мультиигры)
// в группы не объединяется — это отдельная страница из одной статьи.
// Строки с 0 игр пропускаются. Мультистатья скрыта, если все её игры забанены.
$groups = array();   // ключ => [rows]; ключ = игра или '#id' для мультистатьи
$gnames = array();   // ключ => список игр группы
$order  = array();   // порядок появления
foreach(file($GAMES, FILE_IGNORE_NEW_LINES) as $line){
  $line=rtrim(preg_replace('/^\xEF\xBB\xBF/','',$line),"\r");
  if(!preg_match('/^(\d+)\s+(\d+)\s+-\s+(.+)$/u',$line,$m) || (int)$m[2]===0) continue;
  if(!isset($arts[$m[1]])) continue;
  $games=array_values(array_filter(array_map('trim',explode(', ',$m[3])),'strlen'));
  if(!$games) continue;
  $k = count($games)===1 ? $games[0] : '#'.$m[1];
  if(!isset($groups[$k])){ $groups[$k]=array(); $gnames[$k]=$games; $order[]=$k; }
  $groups[$k][]=$arts[$m[1]];
}

// группа видна, если хотя бы одна её игра не забанена
function group_alive($games,$banned){
  foreach($games as $g){ if(!isset($banned[$g])) return true; }
  return false;
}

// активные (небаненные) группы для навигации
$active = array();
foreach($order as $k){ if(group_alive($gnames[$k],$banned)) $active[]=$k; }
$total  = count($active);

$i = isset($_GET['i']) ? (int)$_GET['i']-1 : 0;   // ?i= — номер группы с 1, как в поле ввода
if($i<0) $i=0; if($i>=$total) $i=$total-1;

$cur   = $total ? $active[$i] : null;
$rows  = $cur!==null ? $groups[$cur] : [];
$curGames = $cur!==null ? $gnames[$cur] : [];
$self  = strtok($_SERVER['REQUEST_URI'],'?');

function h($s){ return htmlspecialchars($s, ENT_QUOTES, 'UTF-8'); }

// --- предложка: незабаненные игры той же серии / с тем же началом названия, что и забаненные ---
// Значимые слова названия — без служебных (Online, Mobile, The, of, номера…).
// Игра предлагается, если её значимые слова начинаются с первых двух значимых слов забаненной
// (или с одного, если у забаненной оно единственное: Aion → AION 2, Diablo II → Diablo IV).
function sig_words($g){
  static $skip = array('the','a','an','of','and','is','for','to','in','on','at','online','mobile','mmo','mmorpg','game','remastered','hd','classic',
    'tom','clancys','sid','meiers','ii','iii','iv','v','vi','vii','viii','ix','x','xi','xii','xiii','xiv','xv','xvi');
  $w = preg_split('/[^a-z0-9]+/', strtolower(str_replace(array('&','’',"'"),array(' and ','',''),$g)), -1, PREG_SPLIT_NO_EMPTY);
  return array_values(array_filter($w, function($x) use ($skip){ return !in_array($x,$skip,true) && !ctype_digit($x); }));
}
$sug = array();   // игра => array('banned'=>[...], 'n'=>статей, 'i'=>номер страницы)
$pref = array();  // первое слово => [[префикс-слова, забаненная игра], ...]
foreach(array_keys($banned) as $bn){
  $w=sig_words($bn); $pw=array_slice($w,0,2);
  if(!$pw || (count($pw)===1 && strlen($pw[0])<3)) continue;
  $pref[$pw[0]][]=array($pw,$bn);
}
foreach($active as $n=>$k){
  if($k[0]==='#') continue;                       // мультистатьи не предлагаем
  $w=sig_words($k); if(!$w || !isset($pref[$w[0]])) continue;
  foreach($pref[$w[0]] as $pb){
    if(array_slice($w,0,count($pb[0]))===$pb[0]){
      if(!isset($sug[$k])) $sug[$k]=array('banned'=>array(),'n'=>count($groups[$k]),'i'=>$n+1);
      $sug[$k]['banned'][]=$pb[1];
    }
  }
}
$sugMode = isset($_GET['sug']);
?>
<!doctype html>
<html lang="ru"><head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>MMOHuts — просмотр по играм</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Quicksand:wght@400;500;700&display=swap" rel="stylesheet">
<style>
  :root{--red:#d5001a;--ink:#202020;--gray:#707070;--line:#e2e2e2;--bg:#f2f2f2}
  *{box-sizing:border-box}
  body{font:15px/1.5 'Quicksand',system-ui,Segoe UI,Arial,sans-serif;margin:0;background:var(--bg);color:var(--ink);user-select:none;-webkit-user-select:none;-moz-user-select:none;-ms-user-select:none}
  .gname,.card,.cbody,.t,.t a,.exc{user-select:text;-webkit-user-select:text;-moz-user-select:text;-ms-user-select:text}
  header{position:sticky;top:0;background:#fff;border-bottom:3px solid var(--red);padding:10px 16px;display:flex;gap:12px;align-items:center;flex-wrap:wrap;z-index:5;box-shadow:0 1px 6px rgba(0,0,0,.08)}
  .logo{height:34px;flex:none}
  .nav a,.nav button,#copyAll{background:#fff;color:var(--ink);border:1px solid var(--line);border-radius:6px;padding:8px 12px;text-decoration:none;cursor:pointer;font-family:inherit;font-size:14px;font-weight:500}
  .nav a:hover,.nav button:hover,#copyAll:hover{border-color:var(--red);color:var(--red)}
  .nav a.dis{opacity:.35;pointer-events:none}
  .pos{font-weight:500}
  .gname{font-size:20px;font-weight:700;color:var(--red);text-transform:capitalize}
  .cnt{color:var(--gray)}
  .ban{background:var(--red)!important;border-color:var(--red)!important;color:#fff!important;margin-left:auto;font-weight:700!important}
  .ban:hover{color:#fff!important;filter:brightness(1.08)}
  .jump{margin-left:8px}
  .jump input{width:64px;background:#fff;border:1px solid var(--line);color:var(--ink);border-radius:6px;padding:6px;font-family:inherit}
  main{max-width:1100px;margin:0 auto;padding:16px}
  .card{display:flex;gap:14px;background:#fff;border:1px solid var(--line);border-radius:6px;padding:12px;margin-bottom:12px;transition:box-shadow .15s}
  .card:hover{box-shadow:0 2px 10px rgba(0,0,0,.1)}
  .card img{width:200px;height:112px;object-fit:cover;border-radius:4px;background:#eaeaea;flex:none;user-select:none;-webkit-user-select:none;-moz-user-select:none;-ms-user-select:none;-webkit-user-drag:none}
  .noimg{width:200px;height:112px;border-radius:4px;background:#eaeaea;display:flex;align-items:center;justify-content:center;color:#b0b0b0;font-size:12px;flex:none;user-select:none;-webkit-user-select:none;-moz-user-select:none;-ms-user-select:none}
  .meta{color:var(--gray);font-size:13px;margin-top:6px;user-select:none;-webkit-user-select:none;-moz-user-select:none;-ms-user-select:none}
  .exc{margin-top:6px;font-size:14px;color:#3a3a3a}
  .t{font-size:17px;font-weight:700;line-height:1.3}
  .t a{color:var(--ink);text-decoration:none}
  .t a:hover{color:var(--red)}
  .empty{padding:40px;text-align:center;color:var(--gray)}
  footer{max-width:1100px;margin:0 auto;padding:0 16px 40px;color:var(--gray);font-size:13px}
</style>
</head><body>
<header>
  <a href="https://mmohuts.com/" target="_blank" rel="noopener"><img class="logo" src="https://mmohuts.com/wp-content/uploads/2026/02/cropped-cropped-MMOHuts_Logo-main-opt.png" alt="MMOHuts"></a>
  <div class="nav">
    <a href="<?=h($self)?>?i=1" class="<?=$i<=0?'dis':''?>" style="margin-right:16px">« первая</a>
    <a href="<?=h($self)?>?i=<?=max(1,$i)?>" class="<?=$i<=0?'dis':''?>">‹ назад</a>
    <a href="<?=h($self)?>?i=<?=min($total,$i+2)?>" class="<?=$i>=$total-1?'dis':''?>">вперёд ›</a>
    <span class="jump"><input type="number" id="jump" min="1" max="<?=$total?>" value="<?=$i+1?>" title="номер группы"> /<?=$total?></span>
    <a href="<?=h($self)?>?sug=1" style="margin-left:8px">💡 предложка (<?=count($sug)?>)</a>
  </div>
  <?php if($cur!==null && !$sugMode): ?>
  <span class="pos"><span class="gname"><?=h(implode(', ',$curGames))?></span> <span class="cnt">(<?=count($curGames)>1?'мультиигры, ':''?><?=count($rows)?> статей)</span></span>
  <button type="button" id="copyAll" class="nav" style="margin-left:auto">📋 копировать</button>
  <?php foreach($curGames as $g): if(isset($banned[$g])) continue; ?>
  <form method="post" style="margin-left:8px">
    <input type="hidden" name="game" value="<?=h($g)?>">
    <input type="hidden" name="act" value="ban">
    <button class="ban">🚫 <?=count($curGames)>1 ? h($g) : 'забанить группу'?></button>
  </form>
  <?php endforeach; ?>
  <?php endif; ?>
</header>
<main>
<?php if($sugMode): ?>
  <h2 style="margin:4px 0 12px">💡 Похожие на забаненные (<?=count($sug)?>)</h2>
  <?php if(!$sug): ?><div class="empty">Нечего предложить.</div><?php endif; ?>
  <?php foreach($sug as $g=>$s): ?>
  <div class="card" style="align-items:center">
    <div class="cbody" style="flex:1">
      <div class="t"><a href="<?=h($self)?>?i=<?=$s['i']?>" target="_blank" rel="noopener"><?=h($g)?></a> <span class="cnt">(<?=$s['n']?> статей)</span></div>
      <div class="meta">похожа на забаненные: <?=h(implode(', ',$s['banned']))?></div>
    </div>
    <a class="nav" href="<?=h($self)?>?i=<?=$s['i']?>" target="_blank" rel="noopener" style="border:1px solid var(--line);border-radius:6px;padding:8px 12px;text-decoration:none;color:var(--ink)">👁 открыть</a>
    <form method="post">
      <input type="hidden" name="game" value="<?=h($g)?>">
      <input type="hidden" name="act" value="ban">
      <button class="ban">🚫 забанить</button>
    </form>
  </div>
  <?php endforeach; ?>
<?php elseif($cur===null): ?>
  <div class="empty">Нет активных групп (все забанены или файл пуст).</div>
<?php else: foreach($rows as $r): ?>
  <div class="card">
    <?php if($r['img']!==''): ?>
      <img src="<?=h($r['img'])?>" loading="lazy" alt="">
    <?php else: ?>
      <div class="noimg">нет пикчи</div>
    <?php endif; ?>
    <div class="cbody">
      <div class="t"><a href="<?=h($r['link'])?>" target="_blank" rel="noopener"><?=h($r['title'])?></a></div>
      <div class="meta"><?=h($r['date'])?><?= $r['author']!=='' ? ' · '.h($r['author']) : '' ?></div>
      <?php if($r['excerpt']!==''): ?><div class="exc"><?=h($r['excerpt'])?></div><?php endif; ?>
    </div>
  </div>
<?php endforeach; endif; ?>
</main>
<footer>
  Забанено групп: <?=count($banned)?>. Список в <code>banned.txt</code>.
  <?php if($banned): ?>
    <details><summary>показать забаненные</summary>
      <?php foreach(array_keys($banned) as $b): ?>
        <div style="margin:4px 0">
          <form method="post" style="display:inline">
            <input type="hidden" name="game" value="<?=h($b)?>">
            <input type="hidden" name="act" value="unban">
            <button style="background:#20303a;color:#bfe;border:1px solid #2f4a57;border-radius:6px;padding:2px 8px;cursor:pointer">разбан</button>
          </form>
          <?=h($b)?>
        </div>
      <?php endforeach; ?>
    </details>
  <?php endif; ?>
</footer>
<script>
// переход по номеру группы (в поле и в ?i= один и тот же номер, с 1), без формы -> без алерта
(function(){
  var j=document.getElementById('jump'); if(!j) return;
  var go=function(){ var n=parseInt(j.value,10); if(isNaN(n)) return;
    n=Math.max(1,Math.min(<?=max(1,$total)?>,n));
    location.href = location.pathname + '?i=' + n; };
  j.addEventListener('keydown', function(e){ if(e.key==='Enter'){ e.preventDefault(); go(); } });
  j.addEventListener('change', go);
})();
// ban/unban через fetch — без нативной отправки формы (иначе Firefox ругается на http)
document.querySelectorAll('form[method="post"]').forEach(function(f){
  f.addEventListener('submit', function(ev){
    ev.preventDefault();
    fetch(location.pathname, {method:'POST', body:new FormData(f), headers:{'X-Requested-With':'fetch'}})
      .then(function(){ location.href = location.pathname + location.search; })
      .catch(function(){ location.reload(); });
  });
});
var copyBtn=document.getElementById('copyAll'); if(copyBtn) copyBtn.addEventListener('click', function(){
  var cards = document.querySelectorAll('main .card');
  var out = [];
  cards.forEach(function(c){
    var t = c.querySelector('.t'); var e = c.querySelector('.exc');
    var s = (t?t.innerText.trim():'');
    if(e) s += "\n" + e.innerText.trim();
    if(s) out.push(s);
  });
  var text = out.join("\n\n");
  var btn = this;
  var done = function(){ var o=btn.textContent; btn.textContent='✓ скопировано ('+cards.length+')'; setTimeout(function(){btn.textContent=o;},1500); };
  if(navigator.clipboard && navigator.clipboard.writeText){
    navigator.clipboard.writeText(text).then(done, function(){fallback(text);done();});
  } else { fallback(text); done(); }
  function fallback(txt){ var ta=document.createElement('textarea'); ta.value=txt; document.body.appendChild(ta); ta.select(); try{document.execCommand('copy');}catch(e){} document.body.removeChild(ta); }
});
</script>
</body></html>
