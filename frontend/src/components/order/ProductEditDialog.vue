<template>
  <div>
    <el-dialog
    v-model="visible"
    :title="dialogTitle"
    width="95vw"
    top="3vh"
    :close-on-click-modal="false"
    destroy-on-close
    @closed="onClosed"
  >
    <div v-if="item" ref="dialogBodyRef" class="product-edit-dialog" @click="onDocClick">
      <!-- 基础信息 -->
      <div class="edit-section">
        <div class="section-title" style="background-color: #fde2e2; color: #c45650;">基础信息</div>
        <div class="section-body">
          <div class="basic-info-table">
            <div class="basic-info-label model-label required">客户型号<br /><span>Model</span></div>
            <div class="basic-info-cell model-cell emphasis-cell" data-required-field="customer_model">
              <FieldInput
                v-model="form.customer_model"
                :status="getFieldStatus('customer_model')"
                :disabled="modelLocked"
                @blur="onCustomerModelBlur"
              />
            </div>
            <div class="basic-info-label own-code-label">我司产品编号<br /><span>S.NO.</span></div>
            <div class="basic-info-cell own-code-cell">
              <FieldInput
                v-model="form.factory_code"
                :status="getFieldStatus('company_code')"
                @blur="saveField('company_code', form.factory_code)"
              />
            </div>
            <div class="basic-info-image main-image-cell" data-required-field="image_url" @contextmenu="onImageContextMenu($event, 'main')" @dblclick="onMainImageDblClick">
              <el-upload
                class="image-uploader-main"
                :auto-upload="false"
                :show-file-list="false"
                :on-change="handleImageChange"
              >
                <img v-if="form.image_url" :src="form.image_url" class="preview-image-main" alt="主图" />
                <span v-else class="image-placeholder-text"><el-icon><Plus /></el-icon>主图</span>
              </el-upload>
              <span v-if="!form.image_url" class="main-image-required-star">*</span>
            </div>
            <div class="basic-info-image extra-images-cell">
              <div class="extra-images-scroll">
                <div
                  v-for="(img, idx) in form.extra_images"
                  :key="idx"
                  class="extra-image-item"
                  @contextmenu="onImageContextMenu($event, 'extra', idx)"
                  @dblclick="onExtraImageDblClick(img)"
                >
                  <img :src="img" alt="附图" />
                  <el-icon class="remove-icon" @click="removeExtraImage(idx)"><Close /></el-icon>
                </div>
                <el-upload
                  class="extra-image-uploader"
                  :auto-upload="false"
                  :show-file-list="false"
                  :on-change="handleExtraImageChange"
                >
                  <span class="extra-image-placeholder">
                    <el-icon class="image-placeholder-icon"><Plus /></el-icon>
                    <span v-if="form.extra_images.length === 0" class="extra-image-placeholder-text">附图</span>
                  </span>
                </el-upload>
              </div>
            </div>

            <div class="basic-info-label pname-label required">产品名称<br /><span>P-Name</span></div>
            <div class="basic-info-cell product-name-zh" data-required-field="product_name">
              <el-input
                v-model="form.product_name"
                @blur="saveField('detail_desc', form.product_name)"
              />
            </div>
            <div class="basic-info-cell product-name-en">
              <FieldInput
                v-model="form.product_name_en"
                :status="getFieldStatus('detail_desc_en')"
                @blur="saveField('detail_desc_en', form.product_name_en)"
              />
            </div>
            <div class="basic-info-label short-name-label">产品简称<br /><span>P-Name</span></div>
            <div class="basic-info-cell short-name-zh">
              <FieldInput
                v-model="form.product_short_name"
                :status="getFieldStatus('product_short_name')"
                @blur="saveField('product_short_name', form.product_short_name)"
              />
            </div>
            <div class="basic-info-cell short-name-en">
              <FieldInput
                v-model="form.product_short_name_en"
                :status="getFieldStatus('product_short_name_en')"
                @blur="saveField('product_short_name_en', form.product_short_name_en)"
              />
            </div>
            <div class="basic-info-label oe-label">OE号列表<br /><span>OE-NO.</span></div>
            <div class="basic-info-cell oe-cell">
              <el-input
                v-model="form.oe_number"
                type="textarea"
                :rows="1"
                resize="none"
                @blur="saveField('oe_number', form.oe_number)"
              />
            </div>
            <div class="basic-info-label remark-label">编号备注</div>
            <div class="basic-info-cell remark-cell">
              <el-input
                v-model="form.product_code"
                type="textarea"
                :rows="1"
                resize="none"
                @blur="saveField('customer_code', form.product_code)"
              />
            </div>

            <div class="basic-info-label details-label">产品要求<br /><span>P-Details</span></div>
            <div class="basic-info-cell details-cell">
              <FieldInput
                v-model="form.product_acquires"
                :status="getFieldStatus('product_acquires')"
                @blur="saveField('product_acquires', form.product_acquires)"
              />
            </div>
            <div class="basic-info-label color-label">产品颜色<br /><span>P-color</span></div>
            <div class="basic-info-cell color-cell">
              <FieldInput
                v-model="form.product_color"
                :status="getFieldStatus('product_color')"
                @blur="saveField('product_color', form.product_color)"
              />
            </div>
            <div class="basic-info-label category-label required">产品类别<br /><span>P-Category</span></div>
            <div class="basic-info-cell category-cell" data-required-field="category_id">
              <div class="category-select-group">
                <el-select
                  v-model="categoryLevel1"
                  placeholder="大类"
                  :disabled="categoryLocked"
                  @change="onCategoryLevel1Change"
                >
                  <el-option label="-- 请选择大类 --" value="" />
                  <el-option
                    v-for="category in parentCategories"
                    :key="category.code"
                    :label="category.name"
                    :value="category.code"
                  />
                </el-select>
                <el-select
                  v-model="categoryLevel2"
                  placeholder="子类"
                  :disabled="categoryLocked || !categoryLevel1"
                  @change="onCategoryLevel2Change"
                >
                  <el-option label="-- 请选择子类 --" value="" />
                  <el-option
                    v-for="category in childCategoryOptions"
                    :key="category.code"
                    :label="category.name"
                    :value="category.code"
                  />
                </el-select>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- 销售细节 -->
      <div class="edit-section">
        <div class="section-title" style="background-color: #fde2d8; color: #b85c38;">销售细节</div>
        <div class="section-body">
          <div class="sales-detail-table">
            <!-- 第1行：综合毛利额 + 预估毛利率 + 价格变动 -->
             
             
             
             
            <div class="sales-summary-head">综合毛利额:</div>
            <div class="sales-summary-cell">{{ formatMoney(estimatedProfit) }}</div>
            <div class="sales-summary-head">预估毛利率:</div>
            <div class="sales-summary-cell">{{ estimatedMarginRate }}</div>
            <div class="sales-summary-head">价格变动:</div>
            <div class="sales-summary-cell ">
              <FieldInput
                v-model="form.price_change"
                :status="getFieldStatus('price_change')"
                @blur="onUnmappedBlur('price_change')"
              />
            </div>
            <div class="sales-detail-head span-2">报价备注<br />Q.Notes</div>
            <div class="sales-detail-cell span-3">
              <FieldInput
                v-model="form.quote_remark"
                :status="getFieldStatus('quote_remark')"
                @blur="onUnmappedBlur('quote_remark')"
              />
            </div>
            <!-- 第2行：字段标题 -->
            <div class="sales-detail-head required">采购数量<br />QTY</div>
            <div class="sales-detail-head required">报价<br />PRICE/USD</div>
            <div class="sales-detail-head">金额(USD)<br />TOTAL</div>
            <div class="purchase-cost-head cost-head">预估美金价<br /><span style="font-size:11px;color:#606266">={{ form.purchase_price }}×{{ (1 + form.profit_margin/100).toFixed(2) }}/{{ form.exchange_rate }}</span></div>              
            <div class="purchase-cost-head cost-head required">人民币采购价</div>
            <div class="purchase-cost-head cost-head">贴标费</div>
            <div class="purchase-cost-head cost-head">运费</div>
            <div class="purchase-cost-head cost-head">金额(RMB)</div>
            <div class="sales-detail-head">客户需求<br />Comments</div>
            <div class="sales-detail-head">答复<br />reply</div>
            <div class="sales-detail-head">确定信息<br />confirmation</div>
            
            
            
            <!-- 第3行：字段值 -->
            <div class="sales-detail-cell" data-required-field="quantity">
              <el-input
                v-model="form.quantity"
                type="number"
                style="width: 100%"
                @blur="saveField('quantity', form.quantity)"
              />
            </div>
            <div class="sales-detail-cell" data-required-field="unit_price">
              <el-input
                v-model="form.unit_price"
                type="number"
                style="width: 100%"
                @blur="saveField('unit_price', form.unit_price)"
              >
                <template #prefix>$</template>
              </el-input>
            </div>
            <div class="sales-detail-cell amount-cell">${{ formatMoney(computedAmount) }}</div>
            <div class="purchase-cost-cell cost-cell" style="color:#303133;font-weight:600;line-height:32px;">
                {{ form.estimated_usd_price != null ? '$' + form.estimated_usd_price.toFixed(2) : '-' }}
              </div>
              <div class="purchase-cost-cell cost-cell" data-required-field="purchase_price">
                <el-input
                  v-model="form.purchase_price"
                  type="number"
                  style="width: 100%"
                  @blur="saveField('purchase_price', form.purchase_price)"
                >
                  <template #prefix>¥</template>
                </el-input>
              </div>
              <div class="purchase-cost-cell cost-cell">
                <el-input
                  v-model="form.misc_fee"
                  type="number"
                  style="width: 100%"
                  @blur="saveField('misc_fee', form.misc_fee)"
                >
                  <template #prefix>¥</template>
                </el-input>
              </div>
              <div class="purchase-cost-cell cost-cell">
                <el-input
                  v-model="form.shipping_fee"
                  type="number"
                  style="width: 100%"
                  @blur="saveField('shipping_fee', form.shipping_fee)"
                >
                  <template #prefix>¥</template>
                </el-input>
              </div>
              <div class="purchase-cost-cell cost-cell amount-cell">
                ¥{{ formatMoney(form.purchase_price * form.quantity + (form.misc_fee || 0) + (form.shipping_fee || 0)) }}
              </div>
            <div class="sales-detail-cell">
              <FieldInput
                v-model="form.customer_demand"
                :status="getFieldStatus('customer_demand')"
                @blur="onUnmappedBlur('customer_demand')"
              />
            </div>
            <div class="sales-detail-cell">
              <FieldInput
                v-model="form.reply"
                :status="getFieldStatus('reply')"
                @blur="onUnmappedBlur('reply')"
              />
            </div>
            <div class="sales-detail-cell">
              <FieldInput
                v-model="form.confirm_info"
                :status="getFieldStatus('confirm_info')"
                @blur="onUnmappedBlur('confirm_info')"
              />
            </div>
            
            
              
          </div>
        </div>
      </div>

      <!-- 采购基础信息 -->
      <div class="edit-section">
        <div class="section-title" style="background-color: #e1f3d8; color: #5daf34;">采购基础信息</div>
        <div class="section-body">
          <div class="purchase-cost-table">
              <!-- 第1行：价格 + 开票情况（沿用原表头） -->
            <div class="purchase-cost-head product-detail-head required">产品特性<br />选项/采购备注</div>
            <div class="purchase-cost-cell span-2 product-detail-cell detail-right" data-required-field="product_detail" rowspan="1">
              <el-input
                v-model="form.product_detail"
                type="textarea"
                :rows="3"
                resize="none"
                @blur="saveField('product_detail', form.product_detail)"
              />
            </div>
              <!-- 第3行：供应商 + 产品特性标题 -->
              <div class="purchase-cost-head  required">供应商</div>
              <div class="purchase-cost-cell" data-required-field="supplier_name">
                <el-select
                  v-model="form.supplier"
                  filterable
                  remote
                  :remote-method="searchSuppliers"
                  :loading="supplierLoading"
                  placeholder="搜索或选择供应商"
                  style="width: 100%"
                  :reserve-keyword="false"
                  @change="onSupplierChange"
                >
                  <el-option
                    v-for="s in suppliers"
                    :key="s.id"
                    :label="s.supplier_name"
                    :value="s"
                  >
                    <div class="supplier-option">
                      <span class="supplier-name">{{ s.supplier_name }}</span>
                      <span v-if="s.supplier_code" class="supplier-code">[{{ s.supplier_code }}]</span>
                    </div>
                  </el-option>
                  <template #empty>
                    <div class="supplier-empty">
                      <div v-if="supplierSearchQuery">未找到供应商「{{ supplierSearchQuery }}」</div>
                      <div v-else>暂无供应商数据</div>
                      <el-button
                        v-if="supplierSearchQuery"
                        type="primary"
                        size="small"
                        link
                        @click="openNewSupplierDialog"
                      >
                        + 新建供应商
                      </el-button>
                    </div>
                  </template>
                </el-select>
              </div>
              
              <div class="purchase-cost-head invoice-group-head">开票情况</div>
              <!-- 第4行：供应商链接 + 产品特性内容 -->
              <div class="purchase-cost-head ">供应商链接</div>
              <div class="purchase-cost-cell link-cell">
                <FieldInput
                  v-model="form.shop_url"
                  :status="getFieldStatus('shop_url')"
                  @blur="saveField('shop_url', form.shop_url)"
                />
              </div>
              <div class="purchase-cost-cell invoice-type-cell">
                <el-select
                  v-model="form.invoice_type"
                  placeholder="类型"
                  size="small"
                  style="width: 100%"
                  @change="saveField('invoice_type', form.invoice_type)"
                >
                  <el-option label="增票" value="增票" />
                  <el-option label="普票" value="普票" />
                  <el-option label="不开票" value="不开票" />
                </el-select>
              </div>
              <div class="purchase-cost-cell invoice-rate-cell">
                <el-input
                  v-model="form.invoice_rate"
                  size="small"
                  placeholder="备注"
                  @blur="saveField('invoice_rate', form.invoice_rate)"
                />
              </div>

              <!-- 第5行：采购方式 + 付款标题 -->
              <div class="purchase-cost-head">采购方式</div>
              <div class="purchase-cost-cell">
                <FieldInput
                  v-model="form.purchase_option_name"
                  :status="getFieldStatus('purchase_option_name')"
                  @blur="saveField('purchase_option_name', form.purchase_option_name)"
                />
              </div>
              <div class="purchase-cost-head">付款方式</div>
              <div class="purchase-cost-cell">
                <FieldInput
                  v-model="form.payment_method"
                  :status="getFieldStatus('payment_method')"
                  @blur="saveField('payment_method', form.payment_method)"
                />
              </div>
              <div class="purchase-cost-head payment-head">付款1</div>
              <div class="purchase-cost-head payment-head">付款2</div>
              <div class="purchase-cost-head payment-head">未付款金额</div>

              <!-- 第6行：付款方式 + 付款金额 -->
              <div class="purchase-cost-head">开票工厂（全称）：</div>
              <div class="purchase-cost-cell">
                <FieldInput
                  v-model="form.factory_invoice_name"
                  :status="getFieldStatus('factory_invoice_name')"
                  :disabled="!invoiceFactoryEnabled"
                  @blur="invoiceFactoryEnabled && onUnmappedBlur('factory_invoice_name')"
                />
              </div>
              <div class="purchase-cost-head">货源地</div>
              <div class="purchase-cost-cell">
                <FieldInput
                  v-model="form.source_place"
                  :status="getFieldStatus('source_place')"
                  @blur="onUnmappedBlur('source_place')"
                />
              </div>
              <div class="purchase-cost-cell payment-cell">
                <el-input
                  v-model="form.factory_deposit"
                  type="number"
                  style="width: 100%"
                  @blur="saveField('factory_deposit', form.factory_deposit)"
                />
              </div>
              <div class="purchase-cost-cell payment-cell">
                <el-input
                  v-model="form.factory_balance"
                  type="number"
                  style="width: 100%"
                  @blur="saveField('factory_balance', form.factory_balance)"
                />
              </div>
              <div class="purchase-cost-cell amount-cell payment-cell">
                {{ formatMoney(unpaidAmount) }}
              </div>
              <!-- 第8-10行：包装规格 -->
              <div class="purchase-cost-head packaging-head span-3 required">纸箱包装<br /><span style="font-size:10px;color:#909399;">长×宽×高 (cm)</span></div>
              <div class="purchase-cost-head packaging-head required">
                <span class="packaging-type-label">打包规格</span>
                
              </div>
              <div class="purchase-cost-head packaging-head">整箱毛重(kg)</div>
              <div class="purchase-cost-head packaging-head">预估体积(m³)</div>
              <div class="purchase-cost-head packaging-head">预估毛重(kg)</div>

              <div class="purchase-cost-cell packaging-cell packaging-cell-carton" data-required-field="carton_length">
                <el-input v-model="form.carton_length" placeholder="长" type="number" style="width: 100%" @change="onCartonSizeChange" />
              </div>
              <div class="purchase-cost-cell packaging-cell packaging-cell-carton" data-required-field="carton_width">
                <el-input v-model="form.carton_width" placeholder="宽" type="number" style="width: 100%" @change="onCartonSizeChange" />
              </div>
              <div class="purchase-cost-cell packaging-cell packaging-cell-carton" data-required-field="carton_height">
                <el-input v-model="form.carton_height" placeholder="高" type="number" style="width: 100%" @change="onCartonSizeChange" />
              </div>
              <div class="purchase-cost-cell packaging-cell pack-spec-cell" data-required-field="pack_spec">
                <el-popover ref="packSpecPopoverRef" placement="bottom" :width="260" trigger="click">
                  <template #reference>
                    <el-input :model-value="form.pack_spec || '1pcs/1ctn'" readonly style="width: 100%" />
                  </template>
                  <template #default>
                    <div class="pack-spec-popover">
                      <el-radio-group v-model="form.packaging" @change="onPackagingChange">
                        <el-radio value="1件/箱">1件/箱</el-radio>
                        <el-radio value="多件/箱">多件/箱</el-radio>
                        <el-radio value="1件多箱">1件多箱</el-radio>
                      </el-radio-group>
                      <el-input-number
                        v-if="form.packaging === '多件/箱'"
                        v-model="form.units_per_carton"
                        :min="1"
                        :precision="0"
                        style="width: 100%"
                        @change="updatePackSpec"
                        @blur="onPackSpecBlur"
                      />
                      <el-input-number
                        v-else-if="form.packaging === '1件多箱'"
                        v-model="form.cartons_per_unit"
                        :min="1"
                        :precision="0"
                        style="width: 100%"
                        @change="updatePackSpec"
                        @blur="onPackSpecBlur"
                      />
                      <el-button size="small" type="primary" style="width: 100%" @click="onPackSpecBlur">确定</el-button>
                    </div>
                  </template>
                </el-popover>
              </div>
              <div class="purchase-cost-cell packaging-cell">
                <el-input v-model="form.carton_gross_weight" type="number" style="width: 100%" @change="saveField('carton_gross_weight', form.carton_gross_weight)" />
              </div>
              <div class="purchase-cost-cell packaging-cell">
                <el-input :model-value="form.estimated_volume != null ? form.estimated_volume.toFixed(6) : ''" readonly />
              </div>
              <div class="purchase-cost-cell packaging-cell">
                <el-input :model-value="estimatedGrossWeight" readonly />
              </div>
          </div>
        </div>
      </div>

      <!-- 收货入库信息 -->
      <div class="edit-section">
        <div class="section-title" style="background-color: #d9ecff; color: #409eff;">收货入库信息</div>
        <div class="section-body">
          <div class="inbound-table">
            <div class="inbound-head">纸箱规格 cm</div>
            <div class="inbound-head">箱数 CTN</div>
            <div class="inbound-head">打包规格</div>
            <div class="inbound-head">入库数量</div>
            <div class="inbound-head">入库体积(m³)</div>
            <div class="inbound-head">单箱重量(kg)</div>
            <div class="inbound-head">总重量(kg)</div>

            <div
              v-for="(record, index) in inboundRecords"
              :key="record.id"
              class="inbound-row"
            >
              <div class="inbound-cell carton-size-cell">
                <el-input v-model="record.length" placeholder="长" type="number" @blur="saveInboundRecords" />
                <span>*</span>
                <el-input v-model="record.width" placeholder="宽" type="number" @blur="saveInboundRecords" />
                <span>*</span>
                <el-input v-model="record.height" placeholder="高" type="number" @blur="saveInboundRecords" />
              </div>
              <div class="inbound-cell">
                <el-input v-model="record.carton_count" type="number" @blur="saveInboundRecords" />
              </div>
              <div class="inbound-cell pack-spec-cell">
                <el-popover :ref="(el: any) => { inboundPopoverRefs[index] = el }" placement="bottom" :width="260" trigger="click" @show="currentEditingInboundIndex = index">
                  <template #reference>
                    <el-input :model-value="record.pack_spec || '1pcs/1ctn'" readonly />
                  </template>
                  <template #default>
                    <div class="pack-spec-popover">
                      <el-radio-group v-model="record.packaging" @change="onInboundPackagingChange(record)">
                        <el-radio value="1件/箱">1件/箱</el-radio>
                        <el-radio value="多件/箱">多件/箱</el-radio>
                        <el-radio value="1件多箱">1件多箱</el-radio>
                      </el-radio-group>
                      <el-input-number
                        v-if="record.packaging === '多件/箱'"
                        v-model="record.units_per_carton"
                        :min="1"
                        :precision="0"
                        style="width: 100%"
                        @change="updateInboundPackSpec(record)"
                        @blur="saveInboundRecords"
                      />
                      <el-input-number
                        v-else-if="record.packaging === '1件多箱'"
                        v-model="record.cartons_per_unit"
                        :min="1"
                        :precision="0"
                        style="width: 100%"
                        @change="updateInboundPackSpec(record)"
                        @blur="saveInboundRecords"
                      />
                      <el-button size="small" type="primary" style="width: 100%" @click="saveInboundRecords">确定</el-button>
                    </div>
                  </template>
                </el-popover>
              </div>
              <div class="inbound-cell">
                <el-input v-model="record.stock_in_quantity" type="number" @blur="saveInboundRecords" />
              </div>
              <div class="inbound-cell readonly-cell">{{ calcInboundVolume(record) || '-' }}</div>
              <div class="inbound-cell">
                <el-input v-model="record.carton_weight" type="number" @blur="saveInboundRecords" />
              </div>
              <div class="inbound-cell readonly-cell row-total-weight">
                <span>{{ calcInboundTotalWeight(record) ? calcInboundTotalWeight(record) + 'kgs' : '-' }}</span>
                <el-button
                  v-if="inboundRecords.length > 1"
                  link
                  type="danger"
                  size="small"
                  @click="removeInboundRecord(index)"
                >删除</el-button>
              </div>
            </div>

            <div class="inbound-add-row">
              <el-button type="primary" link :icon="Plus" @click="addInboundRecord">添加新记录</el-button>
            </div>

            <div class="inbound-summary-cell">汇总</div>
            <div class="inbound-summary-cell">{{ inboundSummary.carton_count || '-' }}</div>
            <div class="inbound-summary-cell">\</div>
            <div class="inbound-summary-cell">{{ inboundSummary.stock_in_quantity || '-' }}</div>
            <div class="inbound-summary-cell">{{ inboundSummary.volume || '-' }}</div>
            <div class="inbound-summary-cell">\</div>
            <div class="inbound-summary-cell">{{ inboundSummary.total_weight ? inboundSummary.total_weight + 'kgs' : '-' }}</div>
          </div>
        </div>
      </div>

      <!-- 采购资料存档 -->
      <div class="edit-section">
        <div class="section-title" style="background-color: #f2f6fc; color: #606266;">采购资料存档</div>
        <div class="section-body">
          <div class="form-grid">
            <div v-for="archiveSlot in archiveSlots" :key="archiveSlot.key" class="form-item">
              <label>{{ archiveSlot.label }}</label>
              <el-upload
                :auto-upload="false"
                :show-file-list="false"
                :on-change="createArchiveHandler(archiveSlot.key)"
              >
                <el-button type="primary" size="small" plain>
                  {{ archiveFileNames[archiveSlot.key] ? '重新选择' : '选择文件' }}
                </el-button>
              </el-upload>
              <div v-if="archiveFileNames[archiveSlot.key]" class="archive-file-name">
                {{ archiveFileNames[archiveSlot.key] }}
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <template #footer>
      <el-button @click="requestClose()">关闭</el-button>
      <el-button type="primary" :loading="saving" @click="onSaveClick">保存</el-button>
    </template>
  </el-dialog>

  <!-- 以下组件放在 dialog 外面，避免 destroy-on-close 时 vnode=null 报错 -->
  <!-- 图片预览弹窗 -->
  <ImagePreviewDialog v-model="previewDialog" :src="previewSrc" />

  <!-- 右键菜单 -->
  <div
    v-if="imageMenu.visible"
    class="image-context-menu"
    :style="{ left: imageMenu.x + 'px', top: imageMenu.y + 'px' }"
    @click.stop
  >
    <div v-if="(imageMenu.type === 'main' && form.image_url) || (imageMenu.type === 'extra' && imageMenu.index !== undefined)" class="menu-item" @click="onMenuPreview">预览</div>
    <div class="menu-item" @click="onMenuUpload">{{ imageMenu.type === 'main' && form.image_url ? '更新图片' : '上传图片' }}</div>
    <div v-if="(imageMenu.type === 'main' && form.image_url) || (imageMenu.type === 'extra' && imageMenu.index !== undefined)" class="menu-item" @click="onMenuDelete">删除图片</div>
  </div>

  <!-- 新建供应商弹窗 -->
  <SupplierFormDialog
    v-model="newSupplierDialogVisible"
    :supplier="null"
    @success="onNewSupplierCreated"
  />
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, watch, onMounted, onBeforeUnmount, toRaw } from 'vue'
import { FALLBACK_PARENT_CATEGORIES, FALLBACK_CHILD_CATEGORIES } from '@/constants/productCategories'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, Close } from '@element-plus/icons-vue'
import { useProductEdit, type FieldStatus } from '@/composables/useProductEdit'
import { orderSummaryApi } from '@/api/orderSummary'
import { suppliersApi, type Supplier } from '@/api/suppliers'
import SupplierFormDialog from '@/components/supplier/SupplierFormDialog.vue'
import { apiUrl, assetUrl } from '@/api/base'
import { CUSTOMER_PRODUCTS, PRODUCT_CATEGORIES } from '@/api/endpoints'
import type { OrderDetailItem } from '@/types/orderSummary'
import FieldInput from './FieldInput.vue'
import ImagePreviewDialog from './ImagePreviewDialog.vue'


interface ProductEditItem extends OrderDetailItem {
  customer_name?: string
  customer_country?: string
}

interface ProductCategory {
  code: string
  name: string
  parent_id?: string | null
}

type PackagingType = '1件/箱' | '多件/箱' | '1件多箱'

type InboundRecord = {
  id: string
  length?: number
  width?: number
  height?: number
  carton_count?: number
  packaging: PackagingType
  units_per_carton?: number
  cartons_per_unit?: number
  pack_spec: string
  stock_in_quantity?: number
  carton_weight?: number
}

interface ProductEditForm {
  customer_name: string
  customer_country: string
  customer_model: string
  product_code: string
  image_url: string
  image_url_2: string
  extra_images: string[]
  product_name: string
  product_name_en: string
  product_short_name: string
  product_short_name_en: string
  product_feature: string
  product_acquires: string
  product_color: string
  oe_number: string
  remark: string
  quantity: number
  unit_price: number
  estimated_margin: number | undefined
  price_change: string
  customer_demand: string
  reply: string
  confirm_info: string
  quote_remark: string
  estimated_usd_price: number | undefined
  purchase_price: number
  purchase_currency: 'RMB' | 'USD'
  exchange_rate: number
  profit_margin: number
  misc_fee: number
  shipping_fee: number
  invoice_status: string
  invoice_type: string
  invoice_rate: string
  supplier_name: string
  supplier: Supplier | null
  shop_url: string
  product_detail: string
  purchase_option_name: string
  payment_method: string
  factory_deposit: number | undefined
  factory_balance: number | undefined
  factory_invoice_name: string
  source_place: string
  stock_in_quantity: number
  carton_count: number | undefined
  total_weight: number | undefined
  delivery_date: string
  carton_size: string
  // 包装规格相关字段
  packaging: '1件/箱' | '多件/箱' | '1件多箱'
  units_per_carton: number | undefined
  cartons_per_unit: number | undefined
  pack_spec: string
  factory_code: string
  estimated_volume: number | undefined
  carton_length: number | undefined
  carton_width: number | undefined
  carton_height: number | undefined
  carton_gross_weight: number | undefined
}

const visible = ref(false)
const item = ref<ProductEditItem | null>(null)
const { fieldStates, dirtyFields, saveField } = useProductEdit(item as any)
const categories = ref<ProductCategory[]>([])
const categoryLevel1 = ref('')
const categoryLevel2 = ref('')
const inboundRecords = ref<InboundRecord[]>([])

// 供应商下拉状态
const suppliers = ref<Supplier[]>([])
const supplierLoading = ref(false)
const supplierSearchQuery = ref('')
const newSupplierDialogVisible = ref(false)

const form = reactive<ProductEditForm>({
  customer_name: '',
  customer_country: '',
  customer_model: '',
  product_code: '',
  image_url: '',
  image_url_2: '',
  extra_images: [] as string[],
  product_name: '',
  product_name_en: '',
  product_short_name: '',
  product_short_name_en: '',
  product_feature: '',
  product_acquires: '',
  product_color: '',
  oe_number: '',
  remark: '',
  quantity: 0,
  unit_price: 0,
  estimated_margin: undefined,
  price_change: '',
  customer_demand: '',
  reply: '',
  confirm_info: '',
  quote_remark: '',
  estimated_usd_price: undefined,
  purchase_price: 0,
  purchase_currency: 'RMB',
  exchange_rate: 6.8,
  profit_margin: 25,
  misc_fee: 0,
  shipping_fee: 0,
  invoice_status: '',
  invoice_type: '',
  invoice_rate: '',
  supplier_name: '',
  supplier: null as Supplier | null,
  shop_url: '',
  product_detail: '',
  purchase_option_name: '',
  payment_method: '',
  factory_deposit: undefined,
  factory_balance: undefined,
  factory_invoice_name: '',
  source_place: '',
  stock_in_quantity: 0,
  carton_count: undefined,
  total_weight: undefined,
  delivery_date: '',
  carton_size: '',
  // 包装规格相关字段
  packaging: '1件/箱',
  units_per_carton: undefined,
  cartons_per_unit: undefined,
  pack_spec: '',
  factory_code: '',
  estimated_volume: undefined,
  carton_length: undefined,
  carton_width: undefined,
  carton_height: undefined,
  carton_gross_weight: undefined,
})

const archiveFileNames = reactive<Record<string, string>>({
  contract: '',
  invoice: '',
  payment: '',
  waybill: '',
})

const archiveSlots = [
  { key: 'contract', label: '合同' },
  { key: 'invoice', label: '发票' },
  { key: 'payment', label: '付款凭证' },
  { key: 'waybill', label: '运单凭证' },
]

const dialogTitle = computed(() => {
  const name = item.value?.customer_model || item.value?.product_code || ''
  const customer = item.value?.customer_name
  const customer_country = item.value?.customer_country
  return `编辑产品 - ${name} - ${customer} - ${customer_country}`
})

const parentCategories = computed(() => {
  const parents = categories.value.filter(category => !category.parent_id)
  return parents.length ? parents : FALLBACK_PARENT_CATEGORIES
})

const childCategories = computed(() => {
  const children = categories.value.filter(category => category.parent_id)
  return children.length ? children : FALLBACK_CHILD_CATEGORIES
})

const childCategoryOptions = computed(() => {
  return childCategories.value.filter(category => category.parent_id === categoryLevel1.value)
})

const categoryLocked = computed(() => Boolean(item.value?.category_id))

const modelLocked = ref(false)

const invoiceFactoryEnabled = computed(() => form.invoice_type === '增票' || form.invoice_type === '普票')

const computedAmount = computed(() => {
  const qty = Number(form.quantity || 0)
  const price = Number(form.unit_price || 0)
  return qty * price
})

const purchaseAmount = computed(() => {
  // 采购价 × 数量 + 贴标费 + 运费
  // 采购币种为人民币时，需要除以汇率折算成 USD（与客户报价币种对齐）
  const price = Number(form.purchase_price || 0)
  const qty = Number(form.quantity || 0)
  const misc = Number(form.misc_fee || 0)
  const shipping = Number(form.shipping_fee || 0)
  const rate = Number(form.exchange_rate || 6.8)
  const subtotal = (price * qty + misc + shipping)
  if (form.purchase_currency === 'RMB' && rate > 0) {
    return subtotal / rate
  }
  return subtotal
})

const unpaidAmount = computed(() => {
  const total = purchaseAmount.value
  const deposit = Number(form.factory_deposit || 0)
  const balance = Number(form.factory_balance || 0)
  return total - deposit - balance
})
const estimatedProfit = computed(() => {
  // 综合毛利额 = 美金金额(报价金额) × 汇率 − 采购金额
  const revenue = computedAmount.value
  const rate = Number(form.exchange_rate || 6.8)
  const profit = revenue * rate - purchaseAmount.value
  return Number.isFinite(profit) ? profit : 0
})

const estimatedMarginRate = computed(() => {
  const revenue = computedAmount.value
  const cost = purchaseAmount.value
  if (!revenue) return ''
  const rate = ((revenue - cost) / revenue) * 100
  return `${rate.toFixed(2)}%`
})

// 解析纸箱尺寸字符串为长宽高
function parseCartonSize(sizeStr: string): { l: number; w: number; h: number } {
  const parts = (sizeStr || '').split(/[xX×]/).map(s => parseFloat(s.trim()))
  return {
    l: parts[0] || 0,
    w: parts[1] || 0,
    h: parts[2] || 0,
  }
}

// 根据包装方式计算总箱数
const computedCartonCount = computed(() => {
  const qty = Number(form.quantity || 0)
  if (!qty) return 0
  if (form.packaging === '多件/箱') {
    const upc = Number(form.units_per_carton || 0)
    return upc > 0 ? Math.ceil(qty / upc) : 0
  } else if (form.packaging === '1件多箱') {
    const cpu = Number(form.cartons_per_unit || 0)
    return cpu > 0 ? cpu * qty : 0
  }
  return qty // 1件/箱
})

// 预估毛重 = 整箱毛重 / 每箱件数 × 采购数量 = 单品毛重 × 采购数量
const estimatedGrossWeight = computed(() => {
  const gw = Number(form.carton_gross_weight || 0)
  const qty = Number(form.quantity || 0)
  if (!gw || !qty) return ''
  const unitsPerCarton = form.packaging === '多件/箱'
    ? Number(form.units_per_carton || 0)
    : form.packaging === '1件多箱'
    ? Number(form.cartons_per_unit || 0)
    : 1
  if (unitsPerCarton > 0) {
    return ((gw / unitsPerCarton) * qty).toFixed(2)
  }
  return (gw * qty).toFixed(2)
})

function calcInboundVolume(record: InboundRecord): string {
  const l = Number(record.length || 0)
  const w = Number(record.width || 0)
  const h = Number(record.height || 0)
  const count = Number(record.carton_count || 0)
  if (!l || !w || !h || !count) return ''
  return (((l * w * h) / 1000000) * count).toFixed(5)
}

function calcInboundTotalWeight(record: InboundRecord): string {
  const cartonWeight = Number(record.carton_weight || 0)
  const count = Number(record.carton_count || 0)
  if (!cartonWeight || !count) return ''
  return (cartonWeight * count).toFixed(2)
}

const inboundSummary = computed(() => {
  const summary = inboundRecords.value.reduce(
    (acc, record) => {
      acc.carton_count += Number(record.carton_count || 0)
      acc.stock_in_quantity += Number(record.stock_in_quantity || 0)
      acc.volume += Number(calcInboundVolume(record) || 0)
      acc.total_weight += Number(calcInboundTotalWeight(record) || 0)
      return acc
    },
    { carton_count: 0, stock_in_quantity: 0, volume: 0, total_weight: 0 }
  )

  return {
    carton_count: summary.carton_count,
    stock_in_quantity: summary.stock_in_quantity,
    volume: summary.volume ? summary.volume.toFixed(5) : '',
    total_weight: summary.total_weight ? summary.total_weight.toFixed(2) : '',
  }
})

// 包装方式切换
function onPackagingChange() {
  if (form.packaging === '多件/箱') {
    form.units_per_carton = form.units_per_carton || 1
    form.cartons_per_unit = undefined
  } else if (form.packaging === '1件多箱') {
    form.units_per_carton = undefined
    form.cartons_per_unit = form.cartons_per_unit || 1
  } else {
    form.units_per_carton = undefined
    form.cartons_per_unit = undefined
  }
  updatePackSpec()
}

// 包装方式切换（带保存）
function onPackagingChangeSave() {
  onPackagingChange()
  syncCartonCount()
  updateVolume()
  saveField('packaging', form.packaging)
  saveField('pack_spec', form.pack_spec)
  saveField('carton_count', form.carton_count)
}

// 每箱件数变化（带保存）
function onUnitsPerCartonChange() {
  updatePackSpec()
  syncCartonCount()
  updateVolume()
  saveField('units_per_carton', form.units_per_carton)
  saveField('pack_spec', form.pack_spec)
  saveField('carton_count', form.carton_count)
}

// 每件箱数变化（带保存）
function onCartonsPerUnitChange() {
  updatePackSpec()
  syncCartonCount()
  updateVolume()
  saveField('cartons_per_unit', form.cartons_per_unit)
  saveField('pack_spec', form.pack_spec)
  saveField('carton_count', form.carton_count)
}

// 纸箱尺寸变化（带保存长宽高）
function onCartonSizeChange() {
  updateVolume()
  updateCartonSizeText()
  saveField('carton_length_cm', form.carton_length)
  saveField('carton_width_cm', form.carton_width)
  saveField('carton_height_cm', form.carton_height)
  saveField('carton_size', form.carton_size)
}

// 纸箱尺寸文本变化（带保存）
function onCartonSizeTextChange() {
  saveField('carton_size', form.carton_size)
}

function syncCartonCount() {
  const count = computedCartonCount.value
  form.carton_count = count > 0 ? count : undefined
}

// 加载产品类目（API 优先，空则用硬编码兜底）
async function loadCategories() {
  try {
    const res = await fetch(apiUrl(PRODUCT_CATEGORIES.list))
    if (res.ok) {
      const data = await res.json()
      if (data && data.length) {
        categories.value = data.map((cat: any) => ({
          code: String(cat.code),
          name: cat.name,
          parent_id: cat.parent_id ?? null,
        }))
        return
      }
    }
  } catch { /* fallthrough */ }
  // 硬编码兜底：与旧客户端 client/product_categories.py 保持一致
  categories.value = [
    ...FALLBACK_PARENT_CATEGORIES,
    ...FALLBACK_CHILD_CATEGORIES,
  ]
}

// 大类变化 → 清空子类，重置子类选中值
function onCategoryLevel1Change() {
  categoryLevel2.value = ''
}

// 子类变化 → 首次设置时弹出确认，仅可设置一次
async function onCategoryLevel2Change() {
  if (!categoryLevel2.value) return
  const productId = item.value?.product_id
  const categoryName = childCategories.value.find(c => c.code === categoryLevel2.value)?.name || categoryLevel2.value
  try {
    await ElMessageBox.confirm(
      `产品类目设置为 ${categoryName} 后将无法再次修改，是否确认？`,
      '确认产品类目',
      { type: 'warning', confirmButtonText: '确认', cancelButtonText: '取消' }
    )
  } catch {
    syncCategoryFromItem()
    return
  }
  if (productId) {
    // 已有客户产品：走单独更新接口（不触发 PI item 保存）
    updateCustomerProductCategory(productId, categoryLevel2.value)
  } else {
    // 新产品：直接通过 saveField 写入 PI item
    saveField('category_id', categoryLevel2.value)
  }
}

// 调用客户产品接口更新类目（已有类目后锁定）
async function updateCustomerProductCategory(productId: number, categoryId: string) {
  const prevCategoryId = item.value?.category_id
  if (prevCategoryId) {
    ElMessage.warning('产品类目已设置，不可再次修改')
    // 恢复原值
    syncCategoryFromItem()
    return
  }
  try {
    const res = await fetch(apiUrl(CUSTOMER_PRODUCTS.update(productId)), {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ category_id: categoryId }),
    })
    if (res.ok) {
      const data = await res.json()
      // 锁定类目编辑
      if (item.value) item.value.category_id = data.category_id
      ElMessage.success('产品类目已保存')
    } else {
      const err = await res.json().catch(() => ({}))
      ElMessage.error(err.detail || '保存类目失败')
      syncCategoryFromItem()
    }
  } catch (e: any) {
    ElMessage.error(e.message || '保存类目失败')
    syncCategoryFromItem()
  }
}

// 从 item 回填类目两级选择
function syncCategoryFromItem() {
  const catId = item.value?.category_id
  if (!catId) {
    categoryLevel1.value = ''
    categoryLevel2.value = ''
    return
  }
  // 查找父类
  const childCat = childCategories.value.find(c => c.code === catId)
  if (childCat) {
    categoryLevel1.value = childCat.parent_id || ''
    categoryLevel2.value = catId
  } else {
    // 直接是一级代码（如 'C'）
    categoryLevel1.value = catId
    categoryLevel2.value = ''
  }
}

// 客户型号blur时弹确认，确认后锁定
async function onCustomerModelBlur() {
  if (modelLocked.value) return
  const productId = item.value?.product_id
  if (!productId) {
    // 无客户产品，直接保存并锁定
    await saveField('customer_model', form.customer_model)
    if (form.customer_model) {
      modelLocked.value = true
      if (item.value) item.value.customer_model = form.customer_model
    }
    return
  }
  try {
    await ElMessageBox.confirm(
      `客户型号设置为「${form.customer_model}」后将无法再次修改，是否确认？`,
      '确认客户型号',
      { type: 'warning', confirmButtonText: '确认', cancelButtonText: '取消' }
    )
  } catch {
    // 用户取消，恢复原值
    if (item.value) form.customer_model = item.value.customer_model || ''
    return
  }
  // 确认后更新并锁定
  try {
    const res = await fetch(apiUrl(CUSTOMER_PRODUCTS.update(productId)), {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ customer_model: form.customer_model }),
    })
    if (res.ok) {
      modelLocked.value = true
      if (item.value) item.value.customer_model = form.customer_model
      ElMessage.success('客户型号已保存并锁定')
    } else {
      const err = await res.json().catch(() => ({}))
      ElMessage.error(err.detail || '保存失败')
      if (item.value) form.customer_model = item.value.customer_model || ''
    }
  } catch (e: any) {
    ElMessage.error(e.message || '保存失败')
    if (item.value) form.customer_model = item.value.customer_model || ''
  }
}

// 客户型号锁定：product_id 存在且 customer_model 有非空值时才锁定
function syncModelFromItem() {
  const hasProduct = Boolean(item.value?.product_id)
  const hasModel = Boolean(item.value?.customer_model)
  modelLocked.value = hasProduct && hasModel
  if (item.value) form.customer_model = item.value.customer_model || ''
}

function updateCartonSizeText() {
  const l = Number(form.carton_length || 0)
  const w = Number(form.carton_width || 0)
  const h = Number(form.carton_height || 0)
  form.carton_size = l > 0 && w > 0 && h > 0 ? `${l}x${w}x${h}cm` : ''
}

// 更新打包规格
function updatePackSpec() {
  if (form.packaging === '多件/箱') {
    const upc = Number(form.units_per_carton || 0)
    form.pack_spec = upc > 0 ? `${upc}pcs/1ctn` : ''
  } else if (form.packaging === '1件多箱') {
    const cpu = Number(form.cartons_per_unit || 0)
    form.pack_spec = cpu > 0 ? `1pcs/${cpu}ctn` : ''
  } else {
    form.pack_spec = '1pcs/1ctn'
  }
}

function onPackSpecBlur() {
  updatePackSpec()
  syncCartonCount()
  updateVolume()
  saveField('packaging', form.packaging)
  saveField('units_per_carton', form.units_per_carton)
  saveField('cartons_per_unit', form.cartons_per_unit)
  saveField('pack_spec', form.pack_spec)
  saveField('carton_count', form.carton_count)
  packSpecPopoverRef.value?.hide()
}

function createInboundRecord(record: Partial<InboundRecord> = {}): InboundRecord {
  const inboundRecord: InboundRecord = {
    id: record.id || `${Date.now()}-${Math.random().toString(36).slice(2)}`,
    length: record.length,
    width: record.width,
    height: record.height,
    carton_count: record.carton_count,
    packaging: record.packaging || '1件/箱',
    units_per_carton: record.units_per_carton,
    cartons_per_unit: record.cartons_per_unit,
    pack_spec: record.pack_spec || '',
    stock_in_quantity: record.stock_in_quantity,
    carton_weight: record.carton_weight,
  }
  updateInboundPackSpec(inboundRecord)
  return inboundRecord
}

function updateInboundPackSpec(record: InboundRecord) {
  if (record.packaging === '多件/箱') {
    const upc = Number(record.units_per_carton || 0)
    record.pack_spec = upc > 0 ? `${upc}pcs/1ctn` : ''
  } else if (record.packaging === '1件多箱') {
    const cpu = Number(record.cartons_per_unit || 0)
    record.pack_spec = cpu > 0 ? `1pcs/${cpu}ctn` : ''
  } else {
    record.pack_spec = '1pcs/1ctn'
  }
}

function onInboundPackagingChange(record: InboundRecord) {
  if (record.packaging === '多件/箱') {
    record.units_per_carton = record.units_per_carton || 1
    record.cartons_per_unit = undefined
  } else if (record.packaging === '1件多箱') {
    record.units_per_carton = undefined
    record.cartons_per_unit = record.cartons_per_unit || 1
  } else {
    record.units_per_carton = undefined
    record.cartons_per_unit = undefined
  }
  updateInboundPackSpec(record)
}

function saveInboundRecords() {
  inboundRecords.value.forEach(updateInboundPackSpec)
  saveField('inbound_records', inboundRecords.value.map((record) => ({
    length: Number(record.length || 0) || undefined,
    width: Number(record.width || 0) || undefined,
    height: Number(record.height || 0) || undefined,
    carton_count: Number(record.carton_count || 0) || undefined,
    packaging: record.packaging,
    units_per_carton: Number(record.units_per_carton || 0) || undefined,
    cartons_per_unit: Number(record.cartons_per_unit || 0) || undefined,
    pack_spec: record.pack_spec,
    stock_in_quantity: Number(record.stock_in_quantity || 0) || undefined,
    carton_weight: Number(record.carton_weight || 0) || undefined,
    volume: Number(calcInboundVolume(record) || 0) || undefined,
    total_weight: Number(calcInboundTotalWeight(record) || 0) || undefined,
  })))
  saveField('carton_count', inboundSummary.value.carton_count || undefined)
  saveField('stocked_qty', inboundSummary.value.stock_in_quantity || undefined)
  saveField('total_weight', Number(inboundSummary.value.total_weight || 0) || undefined)
  const idx = currentEditingInboundIndex.value
  if (idx >= 0 && inboundPopoverRefs.value[idx]) {
    inboundPopoverRefs.value[idx].hide()
    currentEditingInboundIndex.value = -1
  }
}

function addInboundRecord() {
  inboundRecords.value.push(createInboundRecord())
}

function removeInboundRecord(index: number) {
  inboundRecords.value.splice(index, 1)
  if (inboundRecords.value.length === 0) {
    inboundRecords.value.push(createInboundRecord())
  }
  saveInboundRecords()
}

// 更新预估体积
function updateVolume() {
  const l = Number(form.carton_length || 0)
  const w = Number(form.carton_width || 0)
  const h = Number(form.carton_height || 0)
  const qty = Number(form.quantity || 0)
  if (l > 0 && w > 0 && h > 0) {
    const cartonVolume = (l * w * h) / 1000000 // CBM per carton
    const unitsPerCarton = form.packaging === '多件/箱'
      ? Number(form.units_per_carton || 0)
      : form.packaging === '1件多箱'
      ? Number(form.cartons_per_unit || 0)
      : 1
    if (unitsPerCarton > 0 && qty > 0) {
      // 单品体积 × 采购数量
      form.estimated_volume = (cartonVolume / unitsPerCarton) * qty
    } else {
      form.estimated_volume = cartonVolume * qty
    }
  } else {
    form.estimated_volume = undefined
  }
}

/**
 * 自动计算预估美金价（采购信息部分）
 *
 * 公式：
 *   - 人民币采购: 预估美金价 = 人民币采购价 × (1 + 毛利率) / 汇率
 *   - 美元采购:   预估美金价 = 美元采购价 × (1 + 毛利率)
 *
 * 当采购价、采购币种、毛利率、汇率任一变化时自动重算。
 */
watch(
  () => [
    form.purchase_price,
    form.purchase_currency,
    form.profit_margin,
    form.exchange_rate,
    form.unit_price,
    form.quantity,
    form.shipping_fee,
    form.misc_fee,
  ],
  () => {
    if (!item.value) return
    const price = Number(form.purchase_price) || 0
    const margin = Number(form.profit_margin) || 0
    const rate = Number(form.exchange_rate) || 6.8
    const factor = 1 + margin / 100
    let usdPrice: number
    if (form.purchase_currency === 'USD') {
      usdPrice = price * factor
    } else {
      if (!rate) return
      usdPrice = (price * factor) / rate
    }
    form.estimated_usd_price = Math.round(usdPrice * 100) / 100

    // 预估毛利率 = (客户美金收入 - 采购总成本USD) / 客户美金收入 * 100
    const unitPrice = Number(form.unit_price) || 0
    const qty = Number(form.quantity) || 0
    const revenue = unitPrice * qty
    const cost = (price * qty + (Number(form.shipping_fee) || 0) + (Number(form.misc_fee) || 0)) / (form.purchase_currency === 'USD' ? 1 : rate)
    if (revenue > 0) {
      const marginRate = ((revenue - cost) / revenue) * 100
      form.estimated_margin = Math.round(marginRate * 100) / 100
    }

    // 同步预估体积（单品体积 × 采购数量）
    updateVolume()
  },
  { immediate: true }
)

// 数量变化时同步更新总箱数（仅在包装方式为多件/箱或1件多箱时生效）
watch(
  () => form.quantity,
  () => {
    if (form.packaging === '多件/箱' || form.packaging === '1件多箱') {
      const count = computedCartonCount.value
      form.carton_count = count > 0 ? count : undefined
    }
  }
)

// 初始化时计算打包规格和体积
onMounted(() => {
  updatePackSpec()
  updateVolume()
  loadCategories()
  window.addEventListener('beforeunload', onBeforeUnload)
})

onBeforeUnmount(() => {
  window.removeEventListener('beforeunload', onBeforeUnload)
})

const emit = defineEmits<{
  (e: 'closed'): void
}>()

function getFieldStatus(field: string): FieldStatus {
  return fieldStates.value[field]?.status || 'idle'
}

function initFromItem(source: ProductEditItem) {
  form.customer_name = source.customer_name || ''
  form.customer_country = source.customer_country || ''
  form.customer_model = source.customer_model || ''
  form.product_code = source.product_code || ''
  form.image_url = assetUrl(source.image_url)
  form.image_url_2 = assetUrl(source.image_url_2)
  // 加载附图列表（从 localStorage 或 source）
  const savedExtraImages = loadExtraImages(source.id)
  form.extra_images = (savedExtraImages || (source.image_url_2 ? [source.image_url_2] : [])).map(assetUrl)
  form.product_name = source.product_name || (source as any).detail_desc || ''
  form.product_name_en = source.product_name_en || (source as any).detail_desc_en || ''
  form.product_short_name = (source as any).product_short_name || ''
  form.product_short_name_en = (source as any).product_short_name_en || ''
  form.product_feature = source.product_feature || ''
  // 产品需求/产品颜色以换行方式存入 remark 字段；读取时按换行拆出
  const remarkText = source.remark || ''
  const remarkLines = remarkText.split(/\r?\n/)
  const remarkRemainLines: string[] = []
  let parsedAcquires = ''
  let parsedColor = ''
  let inAcquires = false
  let inColor = false
  for (const line of remarkLines) {
    const trimmed = line.trim()
    if (trimmed.startsWith('【产品需求】')) {
      inAcquires = true
      inColor = false
      const content = trimmed.replace('【产品需求】', '').trim()
      if (content) parsedAcquires = content
      continue
    }
    if (trimmed.startsWith('【产品颜色】')) {
      inColor = true
      inAcquires = false
      const content = trimmed.replace('【产品颜色】', '').trim()
      if (content) parsedColor = content
      continue
    }
    if (inAcquires) {
      parsedAcquires = parsedAcquires ? `${parsedAcquires}\n${line}` : line
    } else if (inColor) {
      parsedColor = parsedColor ? `${parsedColor}\n${line}` : line
    } else {
      remarkRemainLines.push(line)
    }
  }
  form.product_acquires = (source as any).product_acquires || parsedAcquires || ''
  form.product_color = parsedColor || (source as any).product_color || ''
  form.remark = remarkRemainLines.join('\n').trim()
  form.oe_number = source.oe_number || ''
  form.quantity = source.quantity || 0
  form.unit_price = source.unit_price || 0
  form.estimated_margin = source.estimated_margin ?? undefined
  form.estimated_usd_price = source.estimated_usd_price ?? undefined
  form.purchase_price = source.purchase_price || 0
  // 采购币种/汇率/毛利率优先从源数据读取，否则使用默认值
  form.purchase_currency = (source as any).purchase_currency === 'USD' ? 'USD' : 'RMB'
  form.exchange_rate = (source as any).exchange_rate ?? 6.8
  form.profit_margin = (source as any).profit_margin ?? 25
  form.misc_fee = source.misc_fee || 0
  form.shipping_fee = source.shipping_fee || 0
  form.invoice_status = source.invoice_status || ''
  form.invoice_type = (source as any).invoice_type || ''
  form.invoice_rate = (source as any).invoice_rate || ''
  form.supplier_name = (source as any).supplier_name ?? (source as any).factory_name ?? ''
  form.supplier = null
  form.shop_url = (source as any).shop_url ?? ''
  form.product_detail = source.product_detail || ''
  form.purchase_option_name = source.purchase_option_name || ''
  form.factory_code = (source as any).factory_code || ''
  form.payment_method = (source as any).payment_method || ''
  form.factory_deposit = source.factory_deposit ?? undefined
  form.factory_balance = source.factory_balance ?? undefined
  form.stock_in_quantity = source.stock_in_quantity || 0
  form.carton_count = source.carton_count ?? undefined
  form.total_weight = source.total_weight ?? undefined
  form.delivery_date = source.delivery_date || ''
  form.carton_size = source.carton_size || ''
  // 包装规格相关字段
  form.packaging = (source as any).packaging || '1件/箱'
  form.units_per_carton = (source as any).units_per_carton ?? undefined
  form.cartons_per_unit = (source as any).cartons_per_unit ?? (source as any).boxes_count ?? undefined
  form.pack_spec = (source as any).pack_spec || ''
  if (form.pack_spec) {
    parsePackSpec(form.pack_spec)
  } else {
    updatePackSpec()
  }
  form.factory_code = (source as any).company_code || ''
  form.estimated_volume = (source as any).estimated_volume ?? undefined
  form.carton_gross_weight = (source as any).carton_gross_weight ?? undefined
  // 解析纸箱尺寸字符串回填到长宽高
  const size = parseCartonSize(source.carton_size || '')
  form.carton_length = size.l || ((source as any).carton_length ?? undefined)
  form.carton_width = size.w || ((source as any).carton_width ?? undefined)
  form.carton_height = size.h || ((source as any).carton_height ?? undefined)
  const savedInboundRecords = Array.isArray((source as any).inbound_records) ? (source as any).inbound_records : []
  inboundRecords.value = savedInboundRecords.length > 0
    ? savedInboundRecords.map((record: any) => createInboundRecord({
      id: record.id,
      length: record.length,
      width: record.width,
      height: record.height,
      carton_count: record.carton_count,
      packaging: record.packaging,
      units_per_carton: record.units_per_carton,
      cartons_per_unit: record.cartons_per_unit,
      pack_spec: record.pack_spec,
      stock_in_quantity: record.stock_in_quantity,
      carton_weight: record.carton_weight,
    }))
    : [createInboundRecord({
      length: form.carton_length,
      width: form.carton_width,
      height: form.carton_height,
      carton_count: form.carton_count,
      packaging: form.packaging,
      units_per_carton: form.units_per_carton,
      cartons_per_unit: form.cartons_per_unit,
      pack_spec: form.pack_spec,
      stock_in_quantity: form.stock_in_quantity,
      carton_weight: form.total_weight,
    })]
}

function parsePackSpec(packSpec: string) {
  const match = packSpec.match(/^(\d+)\s*pcs\s*\/\s*(\d+)\s*ctn$/i)
  if (!match) return

  const pcs = Number(match[1])
  const ctn = Number(match[2])
  if (pcs === 1 && ctn === 1) {
    form.packaging = '1件/箱'
    form.units_per_carton = undefined
    form.cartons_per_unit = undefined
  } else if (ctn === 1) {
    form.packaging = '多件/箱'
    form.units_per_carton = pcs
    form.cartons_per_unit = undefined
  } else if (pcs === 1) {
    form.packaging = '1件多箱'
    form.units_per_carton = undefined
    form.cartons_per_unit = ctn
  }
}

function createFormSnapshot() {
  return JSON.stringify({
    form: toRaw(form),
    categoryLevel1: categoryLevel1.value,
    categoryLevel2: categoryLevel2.value,
    inboundRecords: inboundRecords.value.map((r) => toRaw(r)),
  })
}

function open(source: OrderDetailItem, customerName?: string, customerCountry?: string) {
  const editItem = source as ProductEditItem
  editItem.customer_name = customerName || ''
  editItem.customer_country = customerCountry || ''
  item.value = editItem
  initFromItem(editItem)
  syncCategoryFromItem()
  syncModelFromItem()
  // 新增产品时，我司产品编号默认等于客户型号
  if (!editItem.id) {
    form.factory_code = form.customer_model
  }
  // 如果有供应商名称但没有 supplier 对象，自动搜索并匹配
  if (form.supplier_name && !form.supplier) {
    searchSuppliers(form.supplier_name)
  }
  initialFormSnapshot.value = createFormSnapshot()
  visible.value = true
}

function close() {
  visible.value = false
}

async function requestClose(done?: () => void) {
  console.debug('[ProductEdit] requestClose visible=%s hasUnsaved=%s snapshot=%s current=%s',
    visible.value,
    hasUnsavedChanges.value,
    initialFormSnapshot.value.slice(0, 80),
    createFormSnapshot().slice(0, 80),
  )
  if (!hasUnsavedChanges.value) {
    if (typeof done === 'function') done()
    else close()
    return
  }

  try {
    await ElMessageBox.confirm(
      '当前产品编辑内容还有未保存的改动，关闭后这些改动可能丢失。是否继续关闭？',
      '未保存提示',
      { confirmButtonText: '继续关闭', cancelButtonText: '返回编辑', type: 'warning' }
    )
    await ElMessageBox.confirm(
      '请再次确认：仍然关闭并放弃未保存改动吗？',
      '二次确认',
      { confirmButtonText: '确认关闭', cancelButtonText: '返回编辑', type: 'warning' }
    )
    initialFormSnapshot.value = createFormSnapshot()
    if (typeof done === 'function') done()
    else close()
  } catch {
    // 用户取消关闭，保留当前编辑状态
  }
}

function onClosed() {
  modelLocked.value = false
  initialFormSnapshot.value = ''
  emit('closed')
}

function onBeforeUnload(event: BeforeUnloadEvent) {
  if (!hasUnsavedChanges.value) return
  event.preventDefault()
  event.returnValue = ''
}

function onUnmappedBlur(field: string) {
  // 这些字段没有对应的后端列，仅做 UI 展示
  console.debug(`Field ${field} has no backend mapping, skipping save`)
}

function formatMoney(amount: number | string | null | undefined): string {
  if (amount === null || amount === undefined || amount === '') return ''
  const n = Number(amount)
  return isNaN(n) ? '' : n.toFixed(2)
}

function buildRemarkText(): string {
  const parts: string[] = []
  const acquires = (form.product_acquires || '').trim()
  const color = (form.product_color || '').trim()
  if (acquires) parts.push(`【产品需求】\n${acquires}`)
  if (color) parts.push(`【产品颜色】\n${color}`)
  const remark = (form.remark || '').trim()
  if (remark) parts.push(remark)
  return parts.join('\n')
}

function onRemarkBlur() {
  const text = buildRemarkText()
  saveField('remark', text)
}

async function handleImageChange(file: any) {
  try {
    const res = await orderSummaryApi.uploadProductImage(file.raw)
    if (res.data.code === 200) {
      form.image_url = res.data.data.url
      await saveField('image_url', form.image_url)
    } else {
      ElMessage.error(res.data.message || '图片上传失败')
    }
  } catch (e: any) {
    ElMessage.error('图片上传失败: ' + e.message)
  }
}

async function handleImage2Change(file: any) {
  try {
    const res = await orderSummaryApi.uploadProductImage(file.raw)
    if (res.data.code === 200) {
      form.image_url_2 = res.data.data.url
      await saveField('image_url_2', form.image_url_2)
    } else {
      ElMessage.error(res.data.message || '图片上传失败')
    }
  } catch (e: any) {
    ElMessage.error('图片上传失败: ' + e.message)
  }
}

// 上传附图（追加到列表）
async function handleExtraImageChange(file: any) {
  try {
    const res = await orderSummaryApi.uploadProductImage(file.raw)
    if (res.data.code === 200) {
      form.extra_images.push(res.data.data.url)
      saveExtraImages()
    } else {
      ElMessage.error(res.data.message || '图片上传失败')
    }
  } catch (e: any) {
    ElMessage.error('图片上传失败: ' + e.message)
  }
}

// 右键菜单状态
const imageMenu = ref<{ visible: boolean; x: number; y: number; type: 'main' | 'extra'; index?: number }>({
  visible: false,
  x: 0,
  y: 0,
  type: 'main',
})

// 图片预览
const previewDialog = ref(false)
const previewSrc = ref('')
const previewWrapperRef = ref<HTMLElement>()
const dialogBodyRef = ref<HTMLElement>()
const packSpecPopoverRef = ref()
const inboundPopoverRefs = ref<(any | undefined)[]>([])
const currentEditingInboundIndex = ref(-1)
const saving = ref(false)
const initialFormSnapshot = ref('')
const hasUnsavedChanges = computed(() => {
  if (!visible.value) return false
  if (dirtyFields.value.size > 0) return true
  const hasFailedOrSavingField = Object.values(fieldStates.value).some((state) => state.status === 'saving' || state.status === 'error')
  return hasFailedOrSavingField || createFormSnapshot() !== initialFormSnapshot.value
})

function openPreview(src: string) {
  previewSrc.value = src
  previewDialog.value = true
}

function resetPreviewPosition() {
  const el = previewWrapperRef.value
  if (el) {
    el.scrollLeft = 0
    el.scrollTop = 0
  }
}

function onImageContextMenu(e: MouseEvent, type: 'main' | 'extra', index?: number) {
  e.preventDefault()
  // 阻止冒泡，避免外层 click/contextmenu 关闭逻辑立刻把菜单关掉
  e.stopPropagation()
  imageMenu.value = { visible: true, x: e.clientX, y: e.clientY, type, index }
}

function hideImageMenu() {
  imageMenu.value.visible = false
}

function onMenuUpload() {
  hideImageMenu()
  if (imageMenu.value.type === 'main') {
    triggerMainUpload()
  } else {
    triggerExtraUpload(imageMenu.value.index ?? -1)
  }
}

function onMenuDelete() {
  hideImageMenu()
  if (imageMenu.value.type === 'main') {
    if (form.image_url) {
      form.image_url = ''
      saveField('image_url', '')
    }
  } else if (imageMenu.value.index !== undefined) {
    removeExtraImage(imageMenu.value.index)
  }
}

// 触发 el-upload 的文件选择
function triggerMainUpload() {
  const el = document.querySelector('.image-uploader-main .el-upload__input') as HTMLInputElement
  el?.click()
}

function triggerExtraUpload(idx: number) {
  const els = document.querySelectorAll('.extra-image-uploader .el-upload__input')
  const target = els[idx] as HTMLInputElement
  target?.click()
}

function onMenuPreview() {
  hideImageMenu()
  if (imageMenu.value.type === 'main') {
    if (form.image_url) openPreview(form.image_url)
  } else if (imageMenu.value.index !== undefined) {
    openPreview(form.extra_images[imageMenu.value.index])
  }
}

// 点击主图/附图双击预览
function onMainImageDblClick() {
  if (form.image_url) openPreview(form.image_url)
}

function onExtraImageDblClick(img: string) {
  openPreview(img)
}

// 关闭右键菜单
function onDocClick() {
  hideImageMenu()
}

// 移除附图
function removeExtraImage(idx: number) {
  form.extra_images.splice(idx, 1)
  saveExtraImages()
}

const EXTRA_IMAGES_KEY = 'pi_item_extra_images'

function loadExtraImages(itemId: number | undefined): string[] | null {
  if (!itemId) return null
  try {
    const raw = localStorage.getItem(`${EXTRA_IMAGES_KEY}_${itemId}`)
    return raw ? JSON.parse(raw) : null
  } catch {
    return null
  }
}

function saveExtraImages() {
  if (!item.value?.id) return
  try {
    localStorage.setItem(
      `${EXTRA_IMAGES_KEY}_${item.value.id}`,
      JSON.stringify(form.extra_images)
    )
  } catch (e) {
    console.warn('保存附图失败', e)
  }
}

function createArchiveHandler(key: string) {
  return (file: any) => handleArchiveChange(key, file)
}

// 手动保存：校验必填，未填则跳转并标红
async function onSaveClick() {
  const requiredFields: Array<{ key: string; label: string; getVal: () => unknown; positive?: boolean }> = [
    { key: 'customer_model', label: '客户型号', getVal: () => form.customer_model },
    { key: 'image_url', label: '主图', getVal: () => form.image_url },
    { key: 'product_name', label: '产品名称', getVal: () => form.product_name },
    { key: 'category_id', label: '产品类别', getVal: () => categoryLevel2.value || item.value?.category_id },
    { key: 'quantity', label: '采购数量', getVal: () => form.quantity, positive: true },
    { key: 'unit_price', label: '报价', getVal: () => form.unit_price, positive: true },
    { key: 'purchase_price', label: '人民币采购价', getVal: () => form.purchase_price, positive: true },
    { key: 'product_detail', label: '产品特性', getVal: () => form.product_detail },
    { key: 'supplier_name', label: '供应商', getVal: () => form.supplier_name || form.supplier?.supplier_name || '' },
    { key: 'carton_length', label: '纸箱长度', getVal: () => form.carton_length, positive: true },
    { key: 'carton_width', label: '纸箱宽度', getVal: () => form.carton_width, positive: true },
    { key: 'carton_height', label: '纸箱高度', getVal: () => form.carton_height, positive: true },
    { key: 'pack_spec', label: '打包规格', getVal: () => form.pack_spec },
  ]
  const invalidField = requiredFields.find((field) => {
    const value = field.getVal()
    return value === undefined || value === null || value === '' || (field.positive && Number(value) <= 0)
  })
  if (invalidField) {
    const el = dialogBodyRef.value?.querySelector<HTMLElement>(`[data-required-field="${invalidField.key}"]`)
    if (el) {
      const container = dialogBodyRef.value
      if (container) {
        const targetTop = el.getBoundingClientRect().top - container.getBoundingClientRect().top + container.scrollTop - 20
        container.scrollTo({ top: Math.max(targetTop, 0), behavior: 'smooth' })
      } else {
        el.scrollIntoView({ behavior: 'smooth', block: 'center' })
      }
      el.classList.add('required-highlight')
      el.querySelector<HTMLElement>('input, textarea, [tabindex]')?.focus()
      setTimeout(() => el.classList.remove('required-highlight'), 2000)
    }
    ElMessage.warning(`请填写：${invalidField.label}`)
    return
  }

  saving.value = true
  try {
    const fieldsToSave: Array<[string, unknown]> = [
      ['customer_model', form.customer_model],
      ['detail_desc', form.product_name],
      ['quantity', form.quantity],
      ['unit_price', form.unit_price],
      ['purchase_price', form.purchase_price],
      ['product_detail', form.product_detail],
      ['supplier_name', form.supplier_name || form.supplier?.supplier_name || ''],
      ['carton_length_cm', form.carton_length],
      ['carton_width_cm', form.carton_width],
      ['carton_height_cm', form.carton_height],
      ['carton_size', form.carton_size],
      ['packaging', form.packaging],
      ['units_per_carton', form.units_per_carton],
      ['cartons_per_unit', form.cartons_per_unit],
      ['pack_spec', form.pack_spec],
    ]
    await Promise.all(fieldsToSave.map(([field, value]) => saveField(field, value)))
    const failedField = fieldsToSave.find(([field]) => fieldStates.value[field]?.status === 'error')
    if (failedField) {
      ElMessage.error('部分字段保存失败，请检查标红字段')
      return
    }
    initialFormSnapshot.value = createFormSnapshot()
    ElMessage.success('保存成功')
  } finally {
    saving.value = false
  }
}

async function handleArchiveChange(key: string, file: any) {
  archiveFileNames[key] = file.name || ''
  ElMessage.info(`${key} 已选择: ${file.name}`)
}

// 供应商搜索
let supplierSearchTimer: ReturnType<typeof setTimeout> | null = null
async function searchSuppliers(query: string) {
  supplierSearchQuery.value = query
  if (supplierSearchTimer) clearTimeout(supplierSearchTimer)
  if (!query) {
    suppliers.value = []
    return
  }
  supplierSearchTimer = setTimeout(async () => {
    supplierLoading.value = true
    try {
      const res = await suppliersApi.list({ skip: 0, limit: 20, keyword: query })
      suppliers.value = res.data || []
      // 如果有 supplier_name 但尚未匹配到 supplier，自动选中第一个匹配的
      if (!form.supplier && form.supplier_name && suppliers.value.length > 0) {
        const matched = suppliers.value.find(s => s.supplier_name === form.supplier_name)
        if (matched) {
          form.supplier = matched
        } else {
          // 模糊匹配第一个
          form.supplier = suppliers.value[0]
        }
      }
    } catch {
      suppliers.value = []
    } finally {
      supplierLoading.value = false
    }
  }, 300)
}

function onSupplierChange(s: Supplier) {
  form.supplier_name = s.supplier_name
  form.supplier = s
  saveField('supplier_name', s.supplier_name)
}

function openNewSupplierDialog() {
  newSupplierDialogVisible.value = true
}

async function onNewSupplierCreated(created: Supplier) {
  form.supplier_name = created.supplier_name
  form.supplier = created
  saveField('supplier_name', created.supplier_name)
  await searchSuppliers(created.supplier_name)
}

defineExpose({ open, close })
</script>

<style scoped>
.product-edit-dialog {
  max-height: calc(94vh - 100px);
  overflow-y: auto;
  padding-right: 4px;
}

.product-edit-dialog::-webkit-scrollbar {
  width: 8px;
}
.product-edit-dialog::-webkit-scrollbar-thumb {
  background: #c0c4cc;
  border-radius: 4px;
}
.product-edit-dialog::-webkit-scrollbar-track {
  background: #e2f0d9;
}

.edit-section {
  border: 1px solid #ebeef5;
  border-radius: 6px;
  margin-bottom: 10px;
  overflow: hidden;
}

.section-title {
  padding: 7px 12px;
  font-weight: 600;
  font-size: 13px;
}

.section-body {
  padding: 10px 12px;
}

.basic-info-table {
  display: grid;
  grid-template-columns: 105px 1.25fr 105px 1.2fr 90px 1.05fr 105px 1.1fr 95px 1.1fr;
  grid-template-rows: 84px 48px 48px 72px;
  border: 1px solid #222;
  background: #fff;
  overflow: hidden;
}

.basic-info-label,
.basic-info-cell,
.basic-info-image,
.basic-info-action,
.basic-info-plus {
  min-width: 0;
  border-right: 1px solid #222;
  border-bottom: 1px solid #222;
  background: #fff;
}

.basic-info-label {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  text-align: center;
  color: #ff0000;
  font-size: 13px;
  line-height: 1.2;
  font-family: 'Times New Roman', 'SimSun', serif;
}

.basic-info-label.required::before {
  content: '*';
  margin-right: 3px;
}

.basic-info-label span {
  color: #c00000;
  font-size: 12px;
}

.basic-info-cell,
.basic-info-image {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 0 6px;
}

.basic-info-action {
  display: flex;
  align-items: center;
  justify-content: center;
  color: #f56c6c;
  font-size: 13px;
  font-family: 'Times New Roman', 'SimSun', serif;
}

.model-label {
  grid-column: 1;
  grid-row: 1;
}

.model-cell {
  grid-column: 2 / 4;
  grid-row: 1;
}

.emphasis-cell :deep(.el-input__inner),
.emphasis-cell :deep(.field-input .el-input__inner) {
  height: 76px;
  text-align: center;
  font-size: 25px !important;
  line-height: 76px;
  font-family: 'Times New Roman', 'SimSun', serif;
}

.emphasis-cell :deep(.el-input.is-disabled .el-input__wrapper) {
  background: #f2f3f5;
  cursor: not-allowed;
}

.emphasis-cell :deep(.el-input.is-disabled .el-input__inner) {
  color: #606266;
  -webkit-text-fill-color: #606266;
}

.own-code-label {
  grid-column: 4;
  grid-row: 1;
}

.own-code-cell {
  grid-column: 5 / 7;
  grid-row: 1;
  color: #f56c6c;
  font-family: 'Times New Roman', 'SimSun', serif;
  font-size: 13px;
}

.main-image-cell {
  grid-column: 7;
  grid-row: 1;
  padding: 4px;
}

.extra-images-cell {
  grid-column: 8 / 11;
  grid-row: 1;
  padding: 4px 10px;
  justify-content: flex-start;
  border-right: none;
}

.pname-label {
  grid-column: 1;
  grid-row: 2 / 4;
}

.product-name-zh {
  grid-column: 2 / 4;
  grid-row: 2;
  justify-content: flex-start;
}

.product-name-en {
  grid-column: 2 / 4;
  grid-row: 3;
  justify-content: flex-start;
}

.short-name-label {
  grid-column: 4;
  grid-row: 2 / 4;
}

.short-name-zh {
  grid-column: 5 / 7;
  grid-row: 2;
  justify-content: flex-start;
}

.short-name-en {
  grid-column: 5 / 7;
  grid-row: 3;
  justify-content: flex-start;
}

.oe-label {
  grid-column: 7;
  grid-row: 2;
}

.oe-cell {
  grid-column: 8 / 11;
  grid-row: 2;
  align-items: stretch;
  padding: 4px 8px;
  border-right: none;
}

.remark-label {
  grid-column: 7;
  grid-row: 3;
}

.remark-cell {
  grid-column: 8 / 11;
  grid-row: 3;
  align-items: stretch;
  padding: 4px 8px;
  border-right: none;
}

.details-label {
  grid-column: 1;
  grid-row: 4;
}

.details-cell {
  grid-column: 2 / 5;
  grid-row: 4;
  justify-content: flex-start;
  align-items: stretch;
  padding: 4px 8px;
}

.color-label {
  grid-column: 5;
  grid-row: 4;
}

.color-cell {
  grid-column: 6 / 8;
  grid-row: 4;
  justify-content: flex-start;
}

.category-label {
  grid-column: 8;
  grid-row: 4;
}

.category-cell {
  grid-column: 9 / 11;
  grid-row: 4;
  border-right: none;
  overflow: hidden;
}

.category-select-group {
  display: flex;
  gap: 4px;
  width: 100%;
  min-width: 0;
}

.category-select-group .el-select {
  flex: 1;
  min-width: 0;
}

.basic-info-table :deep(.el-input),
.basic-info-table :deep(.el-input-number),
.basic-info-table :deep(.field-input-wrapper) {
  width: 100%;
}

/* 隐藏 el-input-number 的上下箭头按钮 */
:deep(.el-input-number__increase),
:deep(.el-input-number__decrease) {
  display: none !important;
}

.basic-info-table :deep(.el-input__wrapper) {
  box-shadow: none !important;
  border-radius: 0;
  padding: 0;
  background: transparent;
}

.basic-info-table :deep(.el-input__inner) {
  color: #000;
  font-size: 13px;
  text-align: center;
  font-family: 'Times New Roman', 'SimSun', serif;
}

.basic-info-table :deep(.el-input__prefix) {
  color: #000;
}

.basic-info-table :deep(.el-input__wrapper:focus-within),
.basic-info-table :deep(.el-textarea:focus-within) {
  background-color: #fffbe6;
  outline: 2px solid #e6a23c;
  border-radius: 3px;
}

.basic-info-table :deep(.el-textarea),
.basic-info-table :deep(.el-textarea__inner) {
  width: 100%;
  height: 100%;
  resize: none;
  border: none;
  border-radius: 0;
  box-shadow: none;
  padding: 0;
  background: transparent;
  color: #000;
  font-size: 12px;
  font-family: 'Times New Roman', 'SimSun', serif;
}

.form-grid {
  display: grid;
  grid-template-columns: repeat(6, 1fr);
  gap: 8px 10px;
}

.form-grid.info-row-3 {
  grid-template-columns: repeat(3, 1fr);
  margin-bottom: 8px;
}

.form-grid.info-row-4 {
  grid-template-columns: repeat(4, 1fr);
  margin-bottom: 8px;
}

.form-grid.info-row-4:last-child {
  margin-bottom: 0;
}

.form-item {
  display: flex;
  flex-direction: column;
  gap: 3px;
  min-width: 0;
}

.form-item.wide {
  grid-column: span 2;
}

.form-item.half {
  grid-column: span 3;
}

.form-item.all {
  grid-column: span 6;
}

.form-item.tall {
  grid-row: span 2;
}

.form-item.tall :deep(.el-textarea__inner) {
  flex: 1;
  height: 100%;
  min-height: 72px;
}

.form-item.image-item :deep(.el-upload) {
  display: block;
  height: 120px;
}

.form-item label,
.image-cell > label,
.names-block > label {
  font-size: 12px;
  color: #606266;
  line-height: 1.2;
}

.form-item label.required::before,
.image-cell > label.required::before,
.names-block > label.required::before {
  content: '*';
  color: #f56c6c;
}

/* 图片 + 名称紧凑行 */
.compact-image-name-row {
  display: flex;
  align-items: stretch;
  gap: 10px;
  margin-bottom: 8px;
}

.image-cell {
  display: flex;
  flex-direction: column;
  gap: 3px;
  min-width: 0;
}

.main-image-block {
  width: 80px;
  flex-shrink: 0;
}

.extra-image-block {
  width: 360px;
  flex-shrink: 0;
}
/* 采购信息统一表格布局（沿用价格-开票情况，扩展为 5 列多行） */
.purchase-cost-table {
  grid-column: span 6;
  display: grid;
  grid-template-columns: repeat(7, 1fr);
  grid-template-rows: repeat(6, 42px);
  border: 1px solid #222;
  border-radius: 0;
  overflow: hidden;
  background: #fff;
}

.purchase-cost-head {
  display: flex;
  align-items: center;
  justify-content: center;
  background: #e2f0d9;
  border-right: 1px solid #dcdfe6;
  border-bottom: 1px solid #dcdfe6;
  font-size: 13px;
  color: #303133;
  font-weight: 600;
}

.purchase-cost-head:last-of-type {
  border-right: none;
}

.purchase-cost-head.span-2 {
  grid-column: span 2;
}

.purchase-cost-head.span-3 {
  grid-column: span 3;
}

.invoice-group-head {
  grid-column: span 2;
}

.purchase-cost-head.required::before {
  content: '*';
  color: #f56c6c;
  margin-right: 4px;
}

.purchase-cost-cell {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 0 8px;
  border-right: 1px solid #dcdfe6;
  border-bottom: 1px solid #dcdfe6;
  min-width: 0;
}

.purchase-cost-cell:last-child {
  border-right: none;
}

.purchase-cost-cell.span-3 {
  grid-column: span 3;
}

.purchase-cost-cell.span-2 {
  grid-column: span 2;
}

.purchase-cost-cell :deep(.el-input-number),
.purchase-cost-cell :deep(.el-input__wrapper),
.purchase-cost-cell :deep(.field-input-wrapper) {
  width: 100%;
}

.purchase-cost-cell :deep(.el-input__wrapper) {
  box-shadow: none !important;
  border-radius: 0;
  padding: 0;
  background: transparent;
}

.purchase-cost-cell :deep(.el-input__inner) {
  font-size: 12px;
  font-family: 'Times New Roman', 'SimSun', serif;
  text-align: center;
  color: #000;
}

.purchase-cost-cell :deep(.el-input__prefix) {
  color: #000;
}

.purchase-cost-cell :deep(.el-input__wrapper:focus-within) {
  background-color: #fffbe6;
  outline: 2px solid #e6a23c;
  border-radius: 3px;
}

.amount-cell {
  font-size: 16px;
  color: #000;
  font-family: 'Times New Roman', 'SimSun', serif;
}

.invoice-type-cell,
.invoice-rate-cell {
  padding: 0 6px;
}

.product-detail-cell {
  grid-row: span 2;
  align-items: stretch;
  padding: 4px;
}

.detail-right {
  grid-row: span 2;
}

.product-detail-head {
  grid-row: span 2;
  flex-direction: column;
  line-height: 1.3;
  text-align: center;
}

.cost-head,
.cost-cell {
  background: #b7e1a3;
  position: relative;
}

.cost-head:first-child::before {
  content: '';
  position: absolute;
  z-index: 2;
  top: -1px;
  left: -1px;
  width: calc(500% + 4px);
  height: calc(200% + 0px);
  border: 1px solid #000;
  border-radius: 1px;
  pointer-events: none;
}

.payment-head,
.payment-cell {
  background: #c6e0b4;
}

.packaging-head,
.packaging-cell {
  background: #f0f0f0;
}

.packaging-head.span-3 {
  flex-direction: column;
  line-height: 1.2;
  text-align: center;
}

.packaging-type-popover {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.packaging-type-option {
  padding: 6px 12px;
  cursor: pointer;
  border-radius: 4px;
  font-size: 13px;
  color: #303133;
  user-select: none;
}

.packaging-type-option:hover {
  background: #f0f0f0;
}

.packaging-type-option.active {
  background: #b7e1a3;
  color: #000;
  font-weight: 600;
}

.packaging-type-label {
  font-size: 12px;
  color: #303133;
  font-weight: 600;
  white-space: nowrap;
}

.pack-spec-popover {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.pack-spec-popover :deep(.el-radio-group) {
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  gap: 6px;
}

.packaging-cell-carton :deep(.el-input__inner) {
  text-align: center;
  font-size: 14px;
  font-family: 'Times New Roman', 'SimSun', serif;
}

.packaging-cell-carton {
  padding: 0 6px;
}

.product-detail-cell :deep(.el-textarea),
.product-detail-cell :deep(.el-textarea__inner) {
  height: 100%;
  resize: none;
  border-radius: 0;
  border: none;
  padding: 0;
  box-shadow: none;
  font-size: 12px;
  font-family: 'Times New Roman', 'SimSun', serif;
  color: #000;
  background: transparent;
}

.product-detail-cell :deep(.el-textarea:focus-within) {
  background-color: #fffbe6;
  outline: 2px solid #e6a23c;
  border-radius: 3px;
}

.invoice-type-cell :deep(.el-select:focus-within),
.invoice-type-cell :deep(.el-select.is-focused) {
  border-radius: 3px;
  box-shadow: 0 0 0 2px #e6a23c !important;
}

.inbound-table {
  display: grid;
  grid-template-columns: 1.25fr 0.8fr 1fr 1fr 1fr 1fr 1fr;
  border-top: 1px solid #222;
  border-left: 1px solid #222;
  background: #fff;
}

.inbound-row {
  display: contents;
}

.inbound-head,
.inbound-cell,
.inbound-summary-cell {
  min-height: 46px;
  border-right: 1px solid #222;
  border-bottom: 1px solid #222;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 4px 6px;
  box-sizing: border-box;
  font-family: 'Times New Roman', 'SimSun', serif;
  color: #000;
}

.inbound-head {
  font-weight: 600;
  font-size: 15px;
  background: #f7f7f7;
}

.inbound-cell {
  font-size: 14px;
}

.inbound-cell :deep(.el-input__wrapper),
.inbound-cell :deep(.el-input-number),
.inbound-cell :deep(.el-input-number .el-input__wrapper) {
  width: 100%;
  box-shadow: none;
  border-radius: 0;
  background: transparent;
}

.inbound-cell :deep(.el-input__inner) {
  text-align: center;
  font-family: 'Times New Roman', 'SimSun', serif;
  color: #000;
}

.inbound-cell :deep(.el-input__wrapper:focus-within),
.inbound-cell :deep(.el-input-number:focus-within),
.inbound-cell :deep(.el-input-number .el-input__wrapper:focus-within) {
  background-color: #fffbe6;
  outline: 2px solid #e6a23c;
  border-radius: 3px;
}

.carton-size-cell {
  gap: 2px;
}

.carton-size-cell :deep(.el-input__wrapper) {
  padding: 0 2px;
}

.readonly-cell {
  background: #f8fbff;
  font-weight: 500;
}

.row-total-weight {
  gap: 8px;
}

.inbound-summary-cell {
  background: #ffff00;
  font-size: 14px;
  font-weight: 600;
}

.inbound-add-row {
  grid-column: span 7;
  min-height: 38px;
  border-right: 1px solid #222;
  border-bottom: 1px solid #222;
  display: flex;
  align-items: center;
  justify-content: center;
}

/* 销售细节统一表格 */
.sales-detail-table {
  grid-column: span 6;
  display: grid;
  grid-template-columns: repeat(11, 1fr);
  grid-template-rows: 48px 68px 56px;
  border: 1px solid #222;
  border-radius: 0;
  overflow: hidden;
  background: #fff;
}

.sales-summary-head,
.sales-summary-cell {
  display: flex;
  align-items: center;
  justify-content: center;
  background: #f4b8a6;
  border-right: 1px solid #222;
  border-bottom: 1px solid #222;
  font-size: 15px;
  color: #000;
  font-family: 'Times New Roman', 'SimSun', serif;
  min-width: 0;
}

.sales-summary-head {
  justify-content: flex-start;
  padding-left: 4px;
}

.sales-summary-cell.span-2 {
  grid-column: span 2;
}

.sales-summary-cell :deep(.field-input-wrapper),
.sales-summary-cell :deep(.el-input__wrapper) {
  width: 100%;
  box-shadow: none !important;
  border-radius: 0;
  padding: 0 6px;
  background: transparent;
}

.sales-detail-head {
  display: flex;
  align-items: center;
  justify-content: center;
  background: #fbe0d6;
  border-right: 1px solid #222;
  border-bottom: 1px solid #222;
  font-size: 13px;
  color: #303133;
  font-weight: 600;
  text-align: center;
  line-height: 1.3;
  
  padding: 0 4px;
}
.sales-detail-head.span-2 {
  grid-column: span 2;
}
.sales-detail-head:last-of-type {
  border-right: none;
}

.sales-detail-head.required::before {
  content: '*';
  color: #f56c6c;
  margin-right: 4px;
}

.sales-detail-head.vertical-text {
  flex-direction: column;
  font-size: 14px;
  line-height: 1.15;
  letter-spacing: 2px;
  padding: 4px 0;
}

.sales-detail-head.vertical-text .vline {
  display: block;
}

.sales-detail-cell {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 0 8px;
  border-right: 1px solid #222;
  border-bottom: 1px solid #222;
  min-width: 0;
  background: #fdf0eb;
}

.sales-detail-table .cost-head,
.sales-detail-table .cost-cell {
  background: #f7c7a7;
}

.sales-detail-cell:last-child {
  border-right: none;
}

.sales-detail-cell.span-2 {
  grid-column: span 2;
}

.sales-detail-cell.span-3 {
  grid-column: span 3;
}
.sales-detail-cell.span-6 {
  grid-column: span 6;
}

.sales-detail-cell :deep(.el-input-number),
.sales-detail-cell :deep(.el-input__wrapper),
.sales-detail-cell :deep(.field-input-wrapper) {
  width: 100%;
}

.sales-detail-cell :deep(.el-input__wrapper) {
  box-shadow: none !important;
  border-radius: 0;
  padding: 0;
  background: transparent;
}

.sales-detail-cell :deep(.el-input__inner) {
  font-size: 13px;
  font-family: 'Times New Roman', 'SimSun', serif;
  text-align: center;
  color: #000;
}

.sales-detail-cell :deep(.el-input__prefix) {
  color: #000;
}

.sales-detail-cell :deep(.el-input__wrapper:focus-within) {
  background-color: #fffbe6;
  outline: 2px solid #e6a23c;
  border-radius: 3px;
}

/* 产品名称（中英文两行表格布局） */
.name-table-row {
  display: grid;
  grid-template-columns: 80px 1fr;
  grid-template-rows: 1fr 1fr;
  border: 1px solid #dcdfe6;
  border-radius: 4px;
  overflow: hidden;
  height: 100px;
  flex-shrink: 0;
}

.name-label {
  grid-row: 1 / 3;
  grid-column: 1;
  border-right: 1px solid #dcdfe6;
  background: #f5f7fa;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 2px;
  font-size: 12px;
  color: #606266;
  line-height: 1.3;
}

.name-label .required {
  color: #f56c6c;
  font-size: 14px;
}

.name-row-zh {
  grid-column: 2;
  grid-row: 1;
  border-bottom: 1px solid #dcdfe6;
  display: flex;
  flex-direction: column;
}

.name-row-en {
  grid-column: 2;
  grid-row: 1;
  display: flex;
  flex-direction: column;
}

.name-input-label {
  font-size: 11px;
  color: #909399;
  padding: 2px 6px 0;
  background: #fafbfc;
  line-height: 1.4;
}

.name-input-cell {
  flex: 1;
  display: flex;
  align-items: center;
  padding: 0 6px;
}

.name-input-cell :deep(.el-input__wrapper),
.name-input-cell :deep(.field-input-wrapper) {
  box-shadow: none !important;
  border-radius: 0;
  padding: 0;
  background: transparent;
  width: 100%;
}

.name-input-cell :deep(.el-input__inner) {
  font-size: 13px;
  font-family: 'Times New Roman', 'SimSun', serif;
  color: #000;
  text-align: center;
}

/* 全局 small 尺寸 */
.form-item :deep(.el-input__wrapper),
.form-item :deep(.el-textarea__inner) {
  padding: 1px 8px;
  min-height: 26px;
}

.form-item :deep(.el-input__inner) {
  font-size: 12px;
  height: 26px;
  line-height: 26px;
}

.form-item :deep(.el-textarea__inner) {
  font-size: 12px;
  padding: 4px 8px;
}

.form-item :deep(.el-input-number) {
  width: 100%;
}

.form-item :deep(.el-input-number .el-input__inner) {
  font-size: 12px;
  height: 26px;
  line-height: 26px;
}

.form-item :deep(.el-radio-button__inner) {
  padding: 4px 10px;
  font-size: 12px;
}

.form-item :deep(.el-date-editor) {
  --el-date-editor-height: 26px;
}

.form-hint {
  display: block;
  font-size: 11px;
  color: #909399;
  margin-top: 4px;
  line-height: 1.4;
}

/* ============ 主图 80x80 ============ */
.image-uploader-main {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 80px;
  height: 80px;
  border: 1px dashed #d9d9d9;
  border-radius: 4px;
  background: #fafafa;
  cursor: pointer;
  overflow: hidden;
  transition: border-color 0.2s;
}

.image-uploader-main:hover {
  border-color: #409eff;
}

.preview-image-main {
  width: 80px;
  height: 80px;
  object-fit: cover;
  display: block;
}

/* ============ 包装规格 ============ */
.pack-spec-cell {
  width: 100%;
}

.pack-spec-cell :deep(.el-input-number),
.pack-spec-cell :deep(.el-input) {
  width: 100%;
}

/* ============ 附图 360x80 横向滚动 ============ */
.extra-images-scroll {
  display: flex;
  align-items: center;
  gap: 12px;
  width: 100%;
  height: 100%;
  padding: 0 4px;
  border: none;
  border-radius: 0;
  background: transparent;
  overflow-x: auto;
  overflow-y: hidden;
  scrollbar-width: thin;
}

.extra-images-scroll::-webkit-scrollbar {
  height: 6px;
}
.extra-images-scroll::-webkit-scrollbar-thumb {
  background: #c0c4cc;
  border-radius: 3px;
}
.extra-images-scroll::-webkit-scrollbar-track {
  background: #f5f7fa;
}

.extra-image-item {
  position: relative;
  flex-shrink: 0;
  width: 72px;
  height: 72px;
  border-radius: 4px;
  overflow: hidden;
  border: 1px solid #ebeef5;
  background: #fff;
  cursor: pointer;
}

.extra-image-item img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.extra-image-item .remove-icon {
  position: absolute;
  top: 2px;
  right: 2px;
  width: 18px;
  height: 18px;
  border-radius: 50%;
  background: rgba(0, 0, 0, 0.6);
  color: #fff;
  font-size: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  opacity: 0;
  transition: opacity 0.2s;
}

.extra-image-item:hover .remove-icon {
  opacity: 1;
}

.extra-image-uploader {
  flex-shrink: 0;
  width: 64px;
  height: 64px;
  border: none;
  border-radius: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  background: transparent;
  transition: color 0.2s;
}

.extra-image-uploader:hover {
  color: #409eff;
}

.extra-image-placeholder {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 4px;
  width: 100%;
  height: 100%;
}

.extra-image-placeholder-text {
  color: #909399;
  font-size: 12px;
  line-height: 1;
}

.image-placeholder-icon {
  font-size: 20px;
  color: #909399;
}

.image-placeholder-text {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
  color: #c00000;
  font-size: 12px;
}

.main-image-required-star {
  position: absolute;
  top: 2px;
  right: 4px;
  color: #c00000;
  font-size: 16px;
  font-weight: bold;
  pointer-events: none;
  line-height: 1;
}

.main-image-cell {
  position: relative;
}

.extra-image-item {
  cursor: pointer;
}

.image-context-menu {
  position: fixed;
  background: #fff;
  border: 1px solid #e4e7ed;
  border-radius: 4px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.12);
  z-index: 9999;
  padding: 4px 0;
  min-width: 100px;
}

.image-context-menu .menu-item {
  padding: 6px 16px;
  font-size: 13px;
  color: #606266;
  cursor: pointer;
  white-space: nowrap;
}

.image-context-menu .menu-item:hover {
  background: #f5f7fa;
  color: #409eff;
}

.archive-file-name {
  font-size: 12px;
  color: #606266;
  word-break: break-all;
}

/* 必填校验高亮 */
.required-highlight {
  animation: required-flash 0.5s ease-in-out 3;
}
@keyframes required-flash {
  0%, 100% { background-color: transparent; }
  50% { background-color: #fef0f0 !important; }
}
</style>
