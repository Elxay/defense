"""Freeze cache-only scoring schedule and prepare its first input wave."""
from pathlib import Path
import datetime, hashlib, json, subprocess, shutil, fcntl, copy
R=Path('/data/HZX/Def'); U=R/'results/audit/unified300'; T=R/'tools/handoff_20261106'; G=R/'prereg_repo'
def H(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def L(p): return json.loads(Path(p).read_text())
def utc(): return datetime.datetime.now(datetime.timezone.utc).isoformat()
def save(p,x):
    p.parent.mkdir(parents=True,exist_ok=True); q=p.with_suffix('.tmp');q.write_text(json.dumps(x,indent=2)+'\n');q.replace(p)
def publish(files,message):
    with (R/'logs/prereg_publish.lock').open('a') as lk:
        fcntl.flock(lk,fcntl.LOCK_EX)
        assert not subprocess.check_output(['git','status','--porcelain'],cwd=G,text=True).strip()
        rels=[]
        for p in files:
            rel=p.relative_to(R); dst=G/rel; dst.parent.mkdir(parents=True,exist_ok=True); shutil.copy2(p,dst);rels.append(str(rel))
        subprocess.run(['git','add','--',*rels],cwd=G,check=True)
        subprocess.run(['git','diff','--cached','--check'],cwd=G,check=True)
        subprocess.run(['git','commit','-m',message],cwd=G,check=True,capture_output=True)
        subprocess.run(['git','push'],cwd=G,check=True,capture_output=True)
        return subprocess.check_output(['git','rev-parse','HEAD'],cwd=G,text=True).strip()

def main():
    p=U/'scoring_schedule_v1.json'; assert not p.exists()
    h=L(U/'human_reference_plan.json'); old=L(U/'static_alpha0_SORRY_execution_plan.json')
    doc=R/'docs/300_ADDENDUM14_INCREMENTAL_SCORING_AND_ALPHA0_PILOT_CHECK.md'
    doc.write_text('''# 追加14：增量判分、生成与预处理解耦及计时行独立重放

本条仅改变调度及增加用户明确要求的 alpha0 计时行诊断。主轮非零履行标签、效应、INVALID汇总和连贯性统计仍不读取。

1. 已完成家族×条件进入只写缓存判分：SORRY 使用 innet GPU0，WildGuard 使用 node01 GPU2（从此前 GPU0 的节点内调度调整；固定20条门先过）。HarmBench 13B 保持 bf16，使用 innet GPU2+3 独立窗口，不量化、不跨节点拆分。先清已完成英语缓存，再按生成完成事件增量跟进；新任务不得抢外部 innet GPU1。HarmBench 适配与固定20门完成后才启用其双卡窗口；没有将计划写成已启动。
2. 缓存键绑定生成记录文件sha256、提示sha256、完整回复sha256、原始英文指令sha256、预处理sha256、判官及本计划sha256。重新入队先核对来源哈希，任何变化使原键失效，不覆盖原缓存。工人只写逐行结果及覆盖进度，不统计标签或INVALID。
3. 编码alpha0生成与解码分离；生成使用原冻结模型B8/B4、2400、原生模板和零向量20条门，原文回复保留。解码执行门通过前不评分、不读闸门、不生成该家族非零条件。
4. 语言先按冻结langdetect及Qwen3-8B本地翻译链处理alpha0回复，然后只评SORRY。英文原样透传；失败保留INVALID，不按结果换翻译。英语优先，其次中文、法语、编码、印度三语。翻译是B1上限4096的回复翻译，耗时须实测，不使用短指令回译速度外推。
5. PAIR两个目标模型各10条既定计时行，最终提示已固定。对它们使用主轮2400贪心alpha0独立重放一次：共20次生成（10×2，非40）。只读SORRY履行标签与内部早停的交叉表；读取UTC和结果哈希另记。此诊断不影响候选选择、搜索默认参数、alpha或三档预算选择，不涉及非零效应。TAP若另加诊断需独立记录其输入清单。
6. 窗口法与稳态法并报，窗口法继续用于档位。稳态法按均值×行数÷8×2卡，冷启动单列；不是区间上下界。内部早停不等于独立履行；失败/无改善原行为fallback行全部保留，按提示与原行为哈希核对并报告。
7. P1/P2共享同一统计alpha0基线；物理执行与成本不重复计为独立证据。
8. 检测复现原设置资产不足时可做最近现有模型的非原设置复现，但不得称通过原设置复现门。判分积压清理后在单卡窗口预留2–3小时作前向与接口诊断；资产下载不占GPU。原验收线不变。
''')
    plan=dict(utc_frozen=utc(),worker_sha256=H(T/'u300_score_cache_worker.py'),
              doc_sha256=H(doc),**{k:h[k] for k in ['SORRY_parser_sha256','SORRY_prompt_sha256','WG_template_sha256','HB_prompt_source_sha256']},
              SORRY_assets_sha256=old['judge_asset_manifest_sha256'],
              cards={'SORRY':'innet GPU0','WG':'node01 GPU2','HB':'innet GPU2+3; adapter gate pending'},
              scores_only=True,main_effects_read_allowed=False,completed_input_cell_only=True,
              cache_key=['generation_sha256','prompt_sha256','response_sha256','behavior_sha256','preprocessing_sha256','judge','schedule_sha256'],
              priority=['English','Chinese','French','encoding','Indian languages'],
              SORRY_batch=20,WG_batch=8,HB_batch=1,HB_long_input_adapter_admitted=False,
              pilot_diagnostic=dict(algorithm='PAIR',models=['llama','qwen'],rows_per_model=10,
                N_generations=20,cap=2400,greedy=True,read_only='SORRY alpha0 and internal early stop cross table',does_not_change_search_tier=True))
    save(p,plan)
    commit=publish([doc,p,T/'u300_score_cache_worker.py',Path(__file__)],
                   'Freeze incremental cache-only judging schedule and independent alpha0 pilot diagnostic')
    save(U/'scoring_schedule_publication.json',dict(utc=utc(),published=True,commit=commit,plan_sha256=H(p)))
    print(json.dumps(dict(commit=commit,doc_sha256=H(doc),plan_sha256=H(p))))

if __name__=='__main__': main()
