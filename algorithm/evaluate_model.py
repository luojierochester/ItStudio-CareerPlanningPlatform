"""
LightGBM 模型评估脚本（修复版）
使用与训练时相同的特征
"""
import os
import sys
import pandas as pd
import numpy as np
import joblib
import json
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score, f1_score,
    roc_auc_score, confusion_matrix, classification_report,
    precision_recall_curve, roc_curve
)
import matplotlib.pyplot as plt
import seaborn as sns

# 设置中文字体
plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'Arial Unicode MS']
plt.rcParams['axes.unicode_minus'] = False

def load_model_and_data(model_path: str, features_csv: str):
    """加载模型和测试数据"""
    print("📂 加载模型和数据...")
    
    # 加载模型
    if not os.path.exists(model_path):
        print(f"❌ 找不到模型文件：{model_path}")
        return None, None, None, None, None
    
    model_data = joblib.load(model_path)
    
    # 检查模型格式
    if isinstance(model_data, dict):
        print(f"✅ 加载模型字典：{model_path}")
        model = model_data.get('model')
        feature_names = model_data.get('feature_names', None)
        
        if model is None:
            print(f"❌ 模型字典中没有 'model' 键")
            print(f"   可用键：{list(model_data.keys())}")
            return None, None, None, None, None
        
        print(f"   模型类型：{type(model).__name__}")
        if feature_names:
            print(f"   训练时使用的特征：{feature_names}")
    else:
        model = model_data
        feature_names = None
        print(f"✅ 加载模型：{model_path}")
        print(f"   模型类型：{type(model).__name__}")
    
    # 加载特征数据
    if not os.path.exists(features_csv):
        print(f"❌ 找不到特征文件：{features_csv}")
        return None, None, None, None, None
    
    df = pd.read_csv(features_csv)
    print(f"✅ 加载特征数据：{len(df)} 条")
    
    # 确定要使用的特征列
    all_feature_cols = [c for c in df.columns if c not in ['query_id', 'label', 'job_uuid']]
    
    if feature_names:
        # 使用训练时的特征
        feature_cols = feature_names
        print(f"   使用训练时的特征：{feature_cols}")
    else:
        # 如果没有保存特征名，尝试推断
        print(f"   ⚠️  模型未保存特征名，尝试使用前3个特征")
        feature_cols = all_feature_cols[:3]
        print(f"   推断的特征：{feature_cols}")
    
    # 检查特征是否存在
    missing_features = [f for f in feature_cols if f not in df.columns]
    if missing_features:
        print(f"❌ 缺少特征：{missing_features}")
        return None, None, None, None, None
    
    X = df[feature_cols].values
    y = df['label'].values
    
    print(f"   特征维度：{X.shape}")
    print(f"   正样本：{y.sum()} ({y.sum()/len(y):.1%})")
    print(f"   负样本：{len(y) - y.sum()} ({(len(y)-y.sum())/len(y):.1%})")
    
    return model, X, y, feature_cols, df

def evaluate_metrics(y_true, y_pred, y_pred_proba):
    """计算各种评估指标"""
    print("\n" + "="*60)
    print("📊 模型性能指标")
    print("="*60)
    
    # 基础指标
    accuracy = accuracy_score(y_true, y_pred)
    precision = precision_score(y_true, y_pred, zero_division=0)
    recall = recall_score(y_true, y_pred, zero_division=0)
    f1 = f1_score(y_true, y_pred, zero_division=0)
    
    print(f"\n准确率 (Accuracy):  {accuracy:.4f} {'✅' if accuracy > 0.85 else '⚠️' if accuracy > 0.75 else '❌'}")
    print(f"精确率 (Precision): {precision:.4f} {'✅' if precision > 0.75 else '⚠️' if precision > 0.60 else '❌'}")
    print(f"召回率 (Recall):    {recall:.4f} {'✅' if recall > 0.70 else '⚠️' if recall > 0.60 else '❌'}")
    print(f"F1分数 (F1-Score):  {f1:.4f} {'✅' if f1 > 0.75 else '⚠️' if f1 > 0.65 else '❌'}")
    
    # AUC
    if len(np.unique(y_true)) > 1:
        auc = roc_auc_score(y_true, y_pred_proba)
        print(f"AUC:                {auc:.4f} {'✅' if auc > 0.85 else '⚠️' if auc > 0.75 else '❌'}")
    else:
        auc = None
        print("AUC:                无法计算（只有一个类别）")
    
    # 混淆矩阵
    cm = confusion_matrix(y_true, y_pred)
    print(f"\n混淆矩阵：")
    print(f"              预测负  预测正")
    print(f"实际负        {cm[0,0]:6d}  {cm[0,1]:6d}")
    print(f"实际正        {cm[1,0]:6d}  {cm[1,1]:6d}")
    
    # 详细分类报告
    print(f"\n详细分类报告：")
    print(classification_report(y_true, y_pred, target_names=['负样本', '正样本'], zero_division=0))
    
    return {
        'accuracy': accuracy,
        'precision': precision,
        'recall': recall,
        'f1': f1,
        'auc': auc,
        'confusion_matrix': cm
    }

def plot_confusion_matrix(cm, save_path='results/confusion_matrix.png'):
    """绘制混淆矩阵热力图"""
    plt.figure(figsize=(8, 6))
    sns.heatmap(cm, annot=True, fmt='d', cmap='Blues', 
                xticklabels=['预测负', '预测正'],
                yticklabels=['实际负', '实际正'])
    plt.title('混淆矩阵', fontsize=16, pad=20)
    plt.ylabel('真实标签', fontsize=12)
    plt.xlabel('预测标签', fontsize=12)
    plt.tight_layout()
    
    os.makedirs(os.path.dirname(save_path), exist_ok=True)
    plt.savefig(save_path, dpi=300, bbox_inches='tight')
    print(f"✅ 保存混淆矩阵：{save_path}")
    plt.close()

def plot_roc_curve(y_true, y_pred_proba, save_path='results/roc_curve.png'):
    """绘制ROC曲线"""
    if len(np.unique(y_true)) <= 1:
        print("⚠️  无法绘制ROC曲线（只有一个类别）")
        return
    
    fpr, tpr, thresholds = roc_curve(y_true, y_pred_proba)
    auc = roc_auc_score(y_true, y_pred_proba)
    
    plt.figure(figsize=(8, 6))
    plt.plot(fpr, tpr, color='darkorange', lw=2, label=f'ROC curve (AUC = {auc:.4f})')
    plt.plot([0, 1], [0, 1], color='navy', lw=2, linestyle='--', label='Random')
    plt.xlim([0.0, 1.0])
    plt.ylim([0.0, 1.05])
    plt.xlabel('假正率 (False Positive Rate)', fontsize=12)
    plt.ylabel('真正率 (True Positive Rate)', fontsize=12)
    plt.title('ROC曲线', fontsize=16, pad=20)
    plt.legend(loc="lower right")
    plt.grid(alpha=0.3)
    plt.tight_layout()
    
    os.makedirs(os.path.dirname(save_path), exist_ok=True)
    plt.savefig(save_path, dpi=300, bbox_inches='tight')
    print(f"✅ 保存ROC曲线：{save_path}")
    plt.close()

def plot_precision_recall_curve(y_true, y_pred_proba, save_path='results/pr_curve.png'):
    """绘制Precision-Recall曲线"""
    if len(np.unique(y_true)) <= 1:
        print("⚠️  无法绘制PR曲线（只有一个类别）")
        return
    
    precision, recall, thresholds = precision_recall_curve(y_true, y_pred_proba)
    
    plt.figure(figsize=(8, 6))
    plt.plot(recall, precision, color='blue', lw=2)
    plt.xlabel('召回率 (Recall)', fontsize=12)
    plt.ylabel('精确率 (Precision)', fontsize=12)
    plt.title('Precision-Recall曲线', fontsize=16, pad=20)
    plt.grid(alpha=0.3)
    plt.tight_layout()
    
    os.makedirs(os.path.dirname(save_path), exist_ok=True)
    plt.savefig(save_path, dpi=300, bbox_inches='tight')
    print(f"✅ 保存PR曲线：{save_path}")
    plt.close()

def plot_feature_importance(model, feature_names, save_path='results/feature_importance.png'):
    """绘制特征重要性"""
    print("\n" + "="*60)
    print("🔍 特征重要性分析")
    print("="*60)
    
    # 获取特征重要性
    importance = model.feature_importance()
    feature_importance_df = pd.DataFrame({
        'feature': feature_names,
        'importance': importance
    }).sort_values('importance', ascending=False)
    
    print(f"\n特征重要性：")
    for idx, row in feature_importance_df.iterrows():
        print(f"  {row['feature']:30s}: {row['importance']:.4f}")
    
    # 绘图
    plt.figure(figsize=(10, 6))
    plt.barh(range(len(feature_importance_df)), feature_importance_df['importance'].values)
    plt.yticks(range(len(feature_importance_df)), feature_importance_df['feature'].values)
    plt.xlabel('重要性', fontsize=12)
    plt.title('特征重要性', fontsize=16, pad=20)
    plt.gca().invert_yaxis()
    plt.tight_layout()
    
    os.makedirs(os.path.dirname(save_path), exist_ok=True)
    plt.savefig(save_path, dpi=300, bbox_inches='tight')
    print(f"\n✅ 保存特征重要性图：{save_path}")
    plt.close()
    
    return feature_importance_df

def analyze_predictions(y_true, y_pred, y_pred_proba, df, top_n=10):
    """分析预测结果"""
    print("\n" + "="*60)
    print("🔎 预测结果分析")
    print("="*60)
    
    # 添加预测结果到DataFrame
    df_analysis = df.copy()
    df_analysis['y_true'] = y_true
    df_analysis['y_pred'] = y_pred
    df_analysis['y_pred_proba'] = y_pred_proba
    df_analysis['correct'] = (y_true == y_pred)
    
    # 1. 高置信度正确预测
    print(f"\n✅ 高置信度正确预测 (Top {top_n})：")
    correct_high_conf = df_analysis[df_analysis['correct'] == True].nlargest(top_n, 'y_pred_proba')
    for idx, row in correct_high_conf.iterrows():
        print(f"  简历: {row['query_id']}, 真实: {row['y_true']}, 预测: {row['y_pred']}, 置信度: {row['y_pred_proba']:.4f}")
    
    # 2. 假阳性（误报）
    false_positives = df_analysis[(df_analysis['y_true'] == 0) & (df_analysis['y_pred'] == 1)]
    if len(false_positives) > 0:
        print(f"\n❌ 假阳性（误报）样本 (Top {min(top_n, len(false_positives))})：")
        for idx, row in false_positives.nlargest(min(top_n, len(false_positives)), 'y_pred_proba').iterrows():
            print(f"  简历: {row['query_id']}, 置信度: {row['y_pred_proba']:.4f}")
    else:
        print(f"\n✅ 无假阳性样本")
    
    # 3. 假阴性（漏报）
    false_negatives = df_analysis[(df_analysis['y_true'] == 1) & (df_analysis['y_pred'] == 0)]
    if len(false_negatives) > 0:
        print(f"\n❌ 假阴性（漏报）样本 (Top {min(top_n, len(false_negatives))})：")
        for idx, row in false_negatives.nsmallest(min(top_n, len(false_negatives)), 'y_pred_proba').iterrows():
            print(f"  简历: {row['query_id']}, 置信度: {row['y_pred_proba']:.4f}")
    else:
        print(f"\n✅ 无假阴性样本")
    
    return df_analysis

def save_evaluation_report(metrics, feature_importance_df, output_path='results/evaluation_report.json'):
    """保存评估报告"""
    report = {
        'metrics': {
            'accuracy': float(metrics['accuracy']),
            'precision': float(metrics['precision']),
            'recall': float(metrics['recall']),
            'f1': float(metrics['f1']),
            'auc': float(metrics['auc']) if metrics['auc'] is not None else None,
        },
        'confusion_matrix': metrics['confusion_matrix'].tolist(),
        'feature_importance': feature_importance_df.to_dict('records')
    }
    
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    
    print(f"\n✅ 保存评估报告：{output_path}")

def main():
    print("="*60)
    print("🎯 LightGBM 模型评估")
    print("="*60)
    
    # 1. 加载模型和数据
    model_path = "models/lgb/lgb_model.joblib"
    features_csv = "data/features_for_lgb.csv"
    
    model, X, y, feature_cols, df = load_model_and_data(model_path, features_csv)
    
    if model is None:
        return
    
    # 2. 预测
    print("\n🔮 开始预测...")
    try:
        y_pred_proba = model.predict(X)
        print(f"✅ 预测完成，预测概率范围：[{y_pred_proba.min():.4f}, {y_pred_proba.max():.4f}]")
    except Exception as e:
        print(f"❌ 预测失败：{e}")
        return
    
    y_pred = (y_pred_proba >= 0.5).astype(int)
    
    # 3. 评估指标
    metrics = evaluate_metrics(y, y_pred, y_pred_proba)
    
    # 4. 绘制图表
    print("\n📈 生成可视化图表...")
    plot_confusion_matrix(metrics['confusion_matrix'])
    plot_roc_curve(y, y_pred_proba)
    plot_precision_recall_curve(y, y_pred_proba)
    
    # 5. 特征重要性
    feature_importance_df = plot_feature_importance(model, feature_cols)
    
    # 6. 预测结果分析
    df_analysis = analyze_predictions(y, y_pred, y_pred_proba, df, top_n=5)
    
    # 7. 保存评估报告
    save_evaluation_report(metrics, feature_importance_df)
    
    # 8. 保存预测结果
    df_analysis[['query_id', 'label', 'y_true', 'y_pred', 'y_pred_proba']].to_csv(
        'results/predictions.csv', index=False, encoding='utf-8-sig'
    )
    print(f"✅ 保存预测结果：results/predictions.csv")
    
    # 9. 总结
    print("\n" + "="*60)
    print("✅ 评估完成！")
    print("="*60)
    print(f"\n📁 生成文件：")
    print(f"   - results/confusion_matrix.png     (混淆矩阵)")
    print(f"   - results/roc_curve.png            (ROC曲线)")
    print(f"   - results/pr_curve.png             (PR曲线)")
    print(f"   - results/feature_importance.png   (特征重要性)")
    print(f"   - results/evaluation_report.json   (评估报告)")
    print(f"   - results/predictions.csv          (预测结果)")
    
    print(f"\n💡 模型评价：")
    if metrics['accuracy'] > 0.85 and metrics['auc'] and metrics['auc'] > 0.85:
        print(f"   ✅ 模型性能优秀！可以投入使用")
    elif metrics['accuracy'] > 0.75:
        print(f"   ⚠️  模型性能一般，建议优化：")
        if metrics['recall'] < 0.70:
            print(f"      - 召回率偏低，可能漏掉很多匹配岗位")
        if metrics['precision'] < 0.75:
            print(f"      - 精确率偏低，推荐了太多不相关岗位")
    else:
        print(f"   ❌ 模型性能较差，需要重新训练")
        print(f"      建议：增加训练数据或调整特征")

if __name__ == "__main__":
    main()