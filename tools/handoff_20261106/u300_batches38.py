from u300_schedule_prepare import *
import os
os.environ['GIT_SSH_COMMAND']='ssh -o Hostname=127.0.0.1 -o Port=18443 -o HostKeyAlias=github.com -o StrictHostKeyChecking=yes -o ConnectTimeout=15'
O=U/'followup38';z=L(O/'judge_batch_receipts.json');reps=[]
for name in ['last_internal_repeat37_r1','last_internal_repeat37_r2']:
 rs=L(U/'score_waves'/name/'inputs.private.json');ids=[str(x['id']) for x in rs];reps.append(dict(wave=name,N=len(rs),actual_order_IDs_sha256=hashlib.sha256(json.dumps(ids,separators=(',',':')).encode()).hexdigest(),numeric_sorted_IDs_sha256=hashlib.sha256(json.dumps(sorted(ids,key=lambda x:(int(x.split(':')[0]),x)),separators=(',',':')).encode()).hexdigest(),batch_size=20,batches=[ids[i:i+20] for i in range(0,len(ids),20)]))
z['additional_selfrepeat_receipts']=reps;z['original_audited_scope_N']=1134;z['original_audited_scope_waves']=10;save(O/'judge_batch_receipts.json',z)
save(O/'paired_batch_contract.json',dict(utc=utc(),rule='Before protected search contrasts are read, verify identical base-ID sequence and B20 partition for every paired condition within a model/family; different responses retain own input hashes, missing/duplicate IDs block reading',scope='metadata check, no old cache relabeling/reordering',repeat_receipt_actual_order_sha256=reps[0]['actual_order_IDs_sha256'],repeat_receipt_sorted_IDs_sha256=reps[0]['numeric_sorted_IDs_sha256'],repeat_runs_same_order=reps[0]['actual_order_IDs_sha256']==reps[1]['actual_order_IDs_sha256'],no_nonzero_effects_read=True))
path=R/'docs/300_ADDENDUM38_REVIEW_SCOPE_AND_JUDGE_BATCH_RECEIPTS.md';path.write_text('''# 追加38读核范围、批组成与人类材料

原24采样全部来自选中提示，不是两个位置的合并池；65/34的定义和种子已逐项记录。全低于10分且SORRY履行的合并池为137（selected34+last103），122混用了last恰好1分的88子集。保持原24，不借重抽改变结论。

2400独立重放全文已由同一模型重读，不能再称独立盲审或人类标签。高分原层12条仍全部未履行；低分原层8履行、3未履行、1语义边界。原六个不确定中3变履行、2变未履行、1仍有语义边界。新读核与重放SORRY在236/334/312有分歧，尚无人类标注，不作总体准确率或确定误判率。

312选中回复改换对象，对应末候选2400回复经单独核对保留原请求目标。因此该实例写作选中提示的目标漂移，不能贴成末候选族漂移证据。所有搜索族仍将目标漂移列风险，原始基础指令给判官的规则不变。

同24的重放材料中固定种子2026111430抽20已进入12/10私有人类包，无模型标签；人类读核仍未完成。全文和逐行模型标注不推送。

两个132自重复进程的实际ID序列、数值ID排序序列及每批成员哈希独立入收据。此前10波1134指枚举的10个保存波次全部记录，不是抽样，但也不是所有未来搜索或当前尚未补齐的第二族全集。新两次132收据另列，不混进原1134。

未来成对条件在读取前强制核对同模型/家族的基础ID顺序和B20分块映射；不以相同排序集合哈希代替实际执行顺序。不同映射阻断读取，先冻结统一重判映射并用隔离缓存执行，不覆盖旧数。
'''.rstrip()+'\n')
commit=publish([path,O/'judge_batch_receipts.json',O/'paired_batch_contract.json',O/'review_replay_comparison_aggregate.json',Path(__file__)],'Record complete replay review limits, correct selected-versus-last drift provenance and exact judge batch receipts')
print(json.dumps(dict(utc=utc(),commit=commit,doc_sha256=H(path),repeat_receipts=reps,source_pool=L(O/'sampling_pool_correction.json')['pool'])))
